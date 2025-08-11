import os
import re
import json
import uuid
import base64
import time
import requests
from openai import OpenAI

# LangGraph orchestration
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Callable, Optional, Any, Dict, List, TypedDict
from openai import APITimeoutError, APIConnectionError, APIError, RateLimitError

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuildState(TypedDict, total=False):
    user_prompt: str
    options: Dict[str, Any]
    plan: str
    requirements: Dict[str, Any]
    docs_context: List[str]           # chunks from uploaded PDFs/websites
    image_briefs: List[Dict[str, str]]# [{"prompt": "...", "alt": "..."}]
    images: List[Dict[str, str]]      # [{"url": "...", "alt": "..."}]
    code: Dict[str, str]              # {"html": "...", "css": "...", "js": "...}
    modified_code: Dict[str, str]     # {"html": "...", "css": "...", "js": "...}
    change_request: Optional[str]
    target_selector: Optional[str]
    messages: List[Dict[str, str]]
    selectors: List[str]


class GLMClient:
    """
    Client for interacting with GLM-4.5 model via Hugging Face router.
    Also provides a LangGraph agentic pipeline for website generation & scoped edits.
    """
    def __init__(self):
        # Get API key from environment variables
        api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError(
                "API key not found. Please set either HF_TOKEN or HUGGINGFACE_API_KEY "
                "environment variable with your Hugging Face API token."
            )

        # Initialize OpenAI client with Hugging Face router
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=api_key,
        )

        # Chat LLM (GLM-4.5 via Novita route)
        self.model = "zai-org/GLM-4.5:novita"

        # Optionally set an image model for images.generate (router must support it)
        # You can override with env HF_IMAGE_MODEL
        self.image_model = os.environ.get("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")

        # Optional: attach your own vector client externally (e.g., Qdrant)
        self.vector_client = None  # set to your Qdrant client elsewhere

        # Local assets directory for storing generated images/files
        self.assets_dir = os.environ.get("ASSETS_DIR", "./assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        self.max_retries = 3  # Maximum number of retry attempts
        self.initial_backoff = 1  # Initial backoff time in seconds
        self.max_backoff = 60  # Maximum backoff time in seconds
        self._ui_hook: Optional[Callable[[Dict[str, Any]], None]] = None

    # -------------------- Core LLM call --------------------

    def chat_completion(self, messages, temperature=1, max_tokens=10000):
        """
        Chat completion with retry logic for handling timeouts and gateway errors
        """
        start_time = time.time()
        logger.info(f"Starting chat completion with {len(messages)} messages")
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Calculate exponential backoff time
                backoff = min(
                    self.initial_backoff * (2 ** attempt),
                    self.max_backoff
                )
                
                if attempt > 0:
                    logger.info(f"Attempt {attempt + 1}/{self.max_retries} after {backoff}s backoff")
                    time.sleep(backoff)
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=300  # Keep your original timeout
                )
                
                response = completion.choices[0].message.content
                elapsed = time.time() - start_time
                logger.info(f"Chat completion successful in {elapsed:.2f} seconds")
                return response
                
            except (APITimeoutError, APIConnectionError) as e:
                last_exception = e
                logger.warning(f"Timeout/connection error (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    break
                    
            except RateLimitError as e:
                last_exception = e
                # Handle rate limiting with exponential backoff
                retry_after = e.response.headers.get('retry-after') if getattr(e, 'response', None) else None
                if retry_after:
                    try:
                        backoff = min(int(retry_after), self.max_backoff)
                    except ValueError:
                        pass
                
                logger.warning(f"Rate limited (attempt {attempt + 1}), retrying after {backoff}s")
                if attempt == self.max_retries - 1:
                    break
                    
            except APIError as e:
                last_exception = e
                # Retry on server errors (5xx) except 501 (Not Implemented)
                status_code = getattr(e, 'status_code', None)
                if status_code and 500 <= status_code < 600 and status_code != 501:
                    logger.warning(f"Server error {status_code} (attempt {attempt + 1})")
                    if attempt == self.max_retries - 1:
                        break
                else:
                    # Non-retryable error
                    elapsed = time.time() - start_time
                    logger.error(f"Non-retryable error after {elapsed:.2f} seconds: {str(e)}")
                    raise
                    
            except Exception as e:
                last_exception = e
                elapsed = time.time() - start_time
                logger.error(f"Unexpected error after {elapsed:.2f} seconds: {str(e)}")
                raise
        
        # If we exhausted all retries
        elapsed = time.time() - start_time
        logger.error(f"Chat completion failed after {elapsed:.2f} seconds and {self.max_retries} attempts: {str(last_exception)}")
        raise last_exception

    # -------------------- Simple (legacy) generator --------------------

    def generate_website_code(self, prompt, options):
        """
        Legacy: single-pass website generator using GLM-4.5.
        """
        system_prompt = """
        You are an expert web developer specializing in creating modern, responsive websites.
        Generate a complete website based on the user's description.

        Your response should include:
        1. Complete HTML code with semantic structure
        2. CSS code for styling (modern, responsive design)
        3. JavaScript code for interactivity (if needed)

        Format your response as:
        ```html
        [HTML code here]
        ```
        ```css
        [CSS code here]
        ```
        ```javascript
        [JavaScript code here]
        ```
        """

        customization_text = f"""
        Customization requirements:
        - Color scheme: {options['color_scheme']}
        - Font family: {options['font_family']}
        - Layout style: {options['layout']}
        """

        full_prompt = f"{prompt}\n\n{customization_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]

        response_text = self.chat_completion(messages)
        html_code, css_code, js_code = self._split_code_blocks(response_text)
        return html_code, css_code, js_code

    # -------------------- Agentic pipeline --------------------

    def generate_website_code_agentic(
        self,
        prompt: str,
        options: Dict[str, Any],
        change_request: Optional[str] = None,
        target_selector: Optional[str] = None,
        generate_images: bool = True,
        ui_hook: Optional[Callable[[Dict[str, Any]], None]] = None
        ) -> Dict[str, Any]:
        """
        Full multi-agent build:
          think/plan -> gather (RAG) -> images (optional) -> codegen -> maybe modify
        Returns dict with keys:
          plan, requirements, images, code, modified_code, selectors
        """
        self._ui_hook = ui_hook
        initial_state: BuildState = {
            "user_prompt": prompt,
            "options": options or {},
            "docs_context": [],
            "image_briefs": [],
            "images": [],
            "messages": [],
            "change_request": change_request,
            "target_selector": target_selector,
        }

        graph = self._build_graph(generate_images=generate_images)
        memory = MemorySaver()
        app = graph.compile(checkpointer=memory)

        tid = (options or {}).get("thread_id") or f"thread-{uuid.uuid4().hex[:8]}"

        final_state = app.invoke(
            initial_state,
            config={"configurable": {"thread_id": tid, "checkpoint_ns": "build"}}
        )

        # Ensure stable section ids for click-to-edit in preview
        code_block = final_state.get("modified_code") or final_state.get("code") or {}
        html_with_ids, selectors = self._ensure_section_ids(code_block.get("html", ""))

        if final_state.get("modified_code"):
            final_state["modified_code"]["html"] = html_with_ids
        elif final_state.get("code"):
            final_state["code"]["html"] = html_with_ids

        final_state["selectors"] = selectors
        return final_state

    def apply_modification_agentic(
        self,
        current_code: Dict[str, str],
        change_request: str,
        target_selector: Optional[str] = None,
        ui_hook: Optional[Callable[[Dict[str, Any]], None]] = None
        ) -> Dict[str, str]:
        self._ui_hook = ui_hook
        state: BuildState = {
            "code": current_code,
            "modified_code": None,
            "change_request": change_request,
            "target_selector": target_selector,
            "messages": [],
        }

        graph = StateGraph(BuildState)
        graph.add_node("modify", self._node_modify)
        graph.set_entry_point("modify")
        graph.add_edge("modify", END)
        app = graph.compile(checkpointer=MemorySaver())

        tid = current_code.get("thread_id") if isinstance(current_code, dict) else None
        if not tid:
            tid = f"thread-{uuid.uuid4().hex[:8]}"

        out: BuildState = app.invoke(
            state,
            config={"configurable": {"thread_id": tid, "checkpoint_ns": "modify"}}
        )
        return out.get("modified_code") or current_code

    # -------------------- Vector & Image helpers (plug in your stack) --------------------

    def vector_search(self, query: str, top_k: int = 6) -> List[str]:
        """
        Replace this with your Qdrant/FAISS/Chroma search.
        Expected return: List[str] chunk texts (concise).
        """
        if self.vector_client is None:
            return []
        try:
            # Example for Qdrant client (pseudo-code):
            # result = self.vector_client.query(collection_name="site_docs", query_text=query, limit=top_k)
            # return [hit["payload"]["text"] for hit in result]
            return []
        except Exception:
            return []

    def image_generation(self, prompt: str, n: int = 1, size: str = "1024x1024") -> List[Dict[str, str]]:
        """
        Image generation via Hugging Face Inference Router (SDXL).
        Returns: [{"b64": "..."}] for each image generated.
        """
        token = os.getenv("HF_TOKEN")
        if not token:
            return []

        api_url = getattr(
            self,
            "hf_image_api_url",
            "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0",
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Parse "1024x1024" -> width, height. Many endpoints ignore these; safe to include.
        width = height = None
        try:
            w_str, h_str = size.lower().split("x")
            width, height = int(w_str), int(h_str)
        except Exception:
            pass

        out: List[Dict[str, str]] = []
        num = max(1, int(n))
        for _ in range(num):
            payload = {"inputs": prompt}
            if width and height:
                payload["parameters"] = {"width": width, "height": height}

            try:
                resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
                resp.raise_for_status()

                ctype = resp.headers.get("content-type", "")
                # Router returns raw image bytes (e.g., image/png)
                if ctype.startswith("image/") or ctype == "application/octet-stream":
                    b64 = base64.b64encode(resp.content).decode("utf-8")
                    out.append({"b64": b64})
                else:
                    # If an error comes back as JSON/text, skip this image
                    continue
            except Exception:
                continue

        return out

    def save_asset(self, b64: str, filename: str) -> str:
        """
        Save base64 image to assets dir and return a local file URL path (for preview/export).
        """
        path = os.path.join(self.assets_dir, filename)
        try:
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            return path
        except Exception:
            return ""

    def assemble_for_preview(self, code: Dict[str, str]) -> str:
        """Inline CSS and JS into the HTML so a sandboxed preview can render styling and scripts."""
        html = (code.get("html") or "").strip()
        css  = (code.get("css") or "").strip()
        js   = (code.get("js") or "").strip()

        if "<html" not in html.lower():
            html = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'></head><body>{html}</body></html>"

        # inject CSS before </head>
        if re.search(r"</head>", html, flags=re.IGNORECASE):
            html = re.sub(r"</head>", f"<style>{css}</style></head>", html, flags=re.IGNORECASE, count=1)
        else:
            html = html.replace("<body", f"<head><style>{css}</style></head><body", 1)

        # inject JS before </body>
        if re.search(r"</body>", html, flags=re.IGNORECASE):
            html = re.sub(r"</body>", f"<script>{js}</script></body>", html, flags=re.IGNORECASE, count=1)
        else:
            html += f"<script>{js}</script>"
        return html

    def _emit(self, state, event):
        # shrink heavy fields
        def shorten(x, n=1200):
            s = json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else x
            return (s[:n] + " …[truncated]") if len(s) > n else s

        e = dict(event)
        if "summary" in e and isinstance(e["summary"], dict):
            for k, v in list(e["summary"].items()):
                if isinstance(v, (list, dict, str)):
                    e["summary"][k] = shorten(v, 1200)
        if "images" in e and isinstance(e["images"], list) and len(e["images"]) > 3:
            e["images"] = e["images"][:3]

        hook = self._ui_hook
        if callable(hook):
            try:
                hook(e)
            except Exception:
                pass

    # -------------------- Graph definition & nodes --------------------

    def _build_graph(self, generate_images: bool = True):
        g = StateGraph(BuildState)

        g.add_node("think", self._node_think)
        g.add_node("gather", self._node_gather)
        if generate_images:
            g.add_node("image", self._node_image)
        g.add_node("codegen", self._node_codegen)
        g.add_node("maybe_modify", self._node_modify)

        g.set_entry_point("think")
        g.add_edge("think", "gather")
        if generate_images:
            g.add_edge("gather", "image")
            g.add_edge("image", "codegen")
        else:
            g.add_edge("gather", "codegen")

        def route_after_codegen(state: BuildState):
            return "maybe_modify" if state.get("change_request") else END

        g.add_conditional_edges("codegen", route_after_codegen, {"maybe_modify": "maybe_modify", END: END})
        g.add_edge("maybe_modify", END)
        return g

    def _node_think(self, state: BuildState) -> BuildState:
        prompt = state["user_prompt"]
        options = state.get("options", {})
        sys = (
            "You are a senior product designer + web lead. Produce a concise plan to build a modern, "
            "responsive website from the prompt. Identify sitemap, key sections, components, brand tokens, "
            "and risky assumptions that require clarification (but still proceed with best guesses). "
            "Output JSON with keys: plan, sitemap, components, style_tokens, assumptions."
        )
        messages = [{"role": "system", "content": sys},
                    {"role": "user", "content": f"PROMPT:\n{prompt}\n\nOPTIONS:\n{json.dumps(options, indent=2)}"}]
        raw = self.chat_completion(messages)
        try:
            j = json.loads(self._extract_json(raw))
        except Exception:
            j = {"plan": raw, "sitemap": [], "components": [], "style_tokens": {}, "assumptions": []}

        state["plan"] = j.get("plan", "")
        state["requirements"] = {
            "sitemap": j.get("sitemap", []),
            "components": j.get("components", []),
            "style_tokens": j.get("style_tokens", {}),
            "assumptions": j.get("assumptions", []),
            "options": options,
        }
        state.setdefault("messages", []).extend(messages + [{"role": "assistant", "content": raw}])
        self._emit(state, {
            "stage": "think",
            "summary": {
                "plan": state.get("plan", ""),
                "sitemap": state["requirements"].get("sitemap", []),
                "assumptions": state["requirements"].get("assumptions", []),
            }
        })
        return state

    def _node_gather(self, state: BuildState) -> BuildState:
        q = f"Website content ideas, copy, facts, and structure for: {state['user_prompt']}"
        hits = self.vector_search(q, top_k=8) or []
        state["docs_context"] = hits

        sys = (
            "You are a content strategist. Given the plan and retrieved snippets, build a minimal copy deck "
            "for each section in the sitemap. Be concise, scannable, and factual when possible. "
            "Output JSON with keys: copy_deck [{section_id, title, body, bullets?, ctas?}]."
        )
        messages = [
            {"role": "system", "content": sys},
            {"role": "user", "content": f"PLAN:\n{state.get('plan','')}\n\nSITEMAP:\n{json.dumps(state['requirements'].get('sitemap', []), indent=2)}\n\nSNIPPETS:\n{json.dumps(hits, indent=2)}"}
        ]
        raw = self.chat_completion(messages)
        try:
            j = json.loads(self._extract_json(raw))
            state["requirements"]["copy_deck"] = j.get("copy_deck", [])
        except Exception:
            state["requirements"]["copy_deck"] = []
        state.setdefault("messages", []).extend(messages + [{"role": "assistant", "content": raw}])
        self._emit(state, {
            "stage": "gather",
            "summary": {
                "chunks_used": len(state.get("docs_context", [])),
                "sample_chunk": (state.get("docs_context") or [""])[0][:400],
                "sections": [c.get("section_id") for c in state["requirements"].get("copy_deck", [])][:6],
            }
        })
        return state

    def _node_image(self, state: BuildState) -> BuildState:
        sys = (
            "You are a creative director. Produce 2-4 high quality image briefs for the website, "
            "grounded in the copy deck and style tokens. Each brief includes: prompt, alt. "
            "Prefer scenes that look cohesive together. Output JSON: {\"briefs\": [{\"prompt\":\"...\",\"alt\":\"...\"}]}"
        )
        messages = [
            {"role": "system", "content": sys},
            {"role": "user", "content": f"STYLE_TOKENS:\n{json.dumps(state['requirements'].get('style_tokens', {}), indent=2)}\n\nCOPY_DECK:\n{json.dumps(state['requirements'].get('copy_deck', []), indent=2)}"}
        ]
        raw = self.chat_completion(messages)
        briefs = []
        try:
            briefs = json.loads(self._extract_json(raw)).get("briefs", [])
        except Exception:
            for line in raw.splitlines():
                if "prompt:" in line.lower():
                    briefs.append({"prompt": line.split(":", 1)[1].strip(), "alt": "Generated image"})

        state["image_briefs"] = briefs[:4]

        images_out = []
        for i, b in enumerate(state["image_briefs"]):
            try:
                gen = self.image_generation(b["prompt"], n=1, size="1024x1024")
                img = gen[0] if isinstance(gen, list) and gen else {}
                if "b64" in img:
                    # Use data URI for preview reliability
                    data_uri = f"data:image/png;base64,{img['b64']}"
                    images_out.append({"url": data_uri, "alt": b.get("alt", "")})
                    # Optionally save to file system for export
                    _ = self.save_asset(img["b64"], f"image_{i}.png")
                elif "url" in img and img["url"]:
                    images_out.append({"url": img["url"], "alt": b.get("alt", "")})
            except Exception:
                continue
        state["images"] = images_out
        state.setdefault("messages", []).extend(messages + [{"role": "assistant", "content": raw}])
        self._emit(state, {
            "stage": "image",
            "summary": {
                "brief_count": len(state.get("image_briefs", [])),
                "image_count": len(state.get("images", [])),
            },
            "images": state.get("images", [])
        })
        return state

    def _node_codegen(self, state: BuildState) -> BuildState:
        options = state.get("options", {})
        system_prompt = """
        You are an expert web developer specializing in modern, accessible, responsive websites.
        Generate a complete website using semantic HTML, responsive CSS, and JS only if required.
        Return code strictly in three fenced blocks in this exact order: html, css, javascript.
        Do not include any extra commentary outside the fences. Do not minify.
        Use the provided assets by placing <img src="..." alt="..."> with responsive rules (max-width:100%; height:auto).
        """

        customization_text = f"""
        Customization requirements:
        - Color scheme: {options.get('color_scheme', 'auto')}
        - Font family: {options.get('font_family', 'system-ui, sans-serif')}
        - Layout style: {options.get('layout', 'content-first')}
        - Use the following style tokens if present: {json.dumps(state['requirements'].get('style_tokens', {}))}
        """

        assets_text = ""
        if state.get("images"):
            assets_text = "Assets (use placeholders; alt in parentheses):\n" + "\n".join([f"- {{ASSET_{i}}} ({img.get('alt','')})" for i, img in enumerate(state["images"])])

        copy_text = json.dumps(state["requirements"].get("copy_deck", []), indent=2)
        docs_text = "\n".join(state.get("docs_context", [])[:10])

        full_prompt = f"""{state['user_prompt']}

            {customization_text}

            Plan:
            {state.get('plan','')}

            Copy deck:
            {copy_text}

            {assets_text}

            Use any relevant facts from the retrieved snippets below when writing copy, headings, and metadata. Do not fabricate facts.
            Retrieved snippets:
            {docs_text}

            Format your response exactly as three separate fenced code blocks:
            ```html
            [HTML code here]
            ```
            ```css
            [CSS code here]
            ```
            ```javascript
            [JavaScript code here]
            ```
            """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]

        response_text = self.chat_completion(messages)

        def _apply_asset_placeholders(html: str, images: List[Dict[str, str]]) -> str:
            for i, img in enumerate(images):
                html = html.replace(f"{{ASSET_{i}}}", img["url"])
            return html

        html_code, css_code, js_code = self._split_code_blocks(response_text)
        html_code = _apply_asset_placeholders(html_code, state.get("images", []))
        state["code"] = {"html": html_code, "css": css_code, "js": js_code}
        state.setdefault("messages", []).extend(messages + [{"role": "assistant", "content": response_text}])
        self._emit(state, {
            "stage": "codegen",
            "summary": {
                "html_chars": len(state["code"].get("html", "")),
                "css_chars": len(state["code"].get("css", "")),
                "js_chars": len(state["code"].get("js", "")),
            }
        })
        return state

    def _node_modify(self, state: BuildState) -> BuildState:
        current = state.get("modified_code") or state.get("code") or {"html": "", "css": "", "js": ""}
        change = state.get("change_request") or ""
        selector = state.get("target_selector")

        sys = (
            "You are a precise code editor for HTML/CSS/JS websites. "
            "Given the current code and an edit request, update the minimal necessary parts. "
            "If a target selector is provided, restrict changes to that section only. "
            "Return THREE fenced blocks in this exact order (html, css, javascript). "
            "If a block is unchanged, return it unchanged. Do not add commentary."
        )
        user_content = f"""
Edit request: {change}
Target selector (optional): {selector or '(none)'}
Current HTML:
{current.get('html','')}

Current CSS:
{current.get('css','')}

Current JS:
{current.get('js','')}

Return exactly three separate fenced blocks:
```html
[UPDATED HTML]
```
```css
[UPDATED CSS]
```
```javascript
[UPDATED JS]
```
"""
        messages = [{"role": "system", "content": sys}, {"role": "user", "content": user_content}]
        out = self.chat_completion(messages)
        new_html, new_css, new_js = self._split_code_blocks(out)
        state["modified_code"] = {
            "html": new_html or current["html"],
            "css": new_css or current["css"],
            "js": new_js or current["js"]
        }
        state.setdefault("messages", []).extend(messages + [{"role": "assistant", "content": out}])
        self._emit(state, {
            "stage": "modify",
            "summary": {
                "selector": state.get("target_selector"),
                "html_chars": len(state["modified_code"].get("html", "")),
                "css_chars": len(state["modified_code"].get("css", "")),
                "js_chars": len(state["modified_code"].get("js", "")),
            }
        })
        return state

    # -------------------- Utilities --------------------

    @staticmethod
    def _split_code_blocks(response_text: str) -> (str, str, str):
        """
        Robustly parse ```html / ```css / ```javascript fences in any order, return strings.
        Also supports a fallback where the model returned a single block with markers 'css' and 'javascript'.
        """
        html_code = css_code = js_code = ""
        parts = response_text.split("```")
        # Iterate over code fences
        for i in range(1, len(parts), 2):
            header_and_body = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ""
            if "\n" in header_and_body:
                lang, code = header_and_body.split("\n", 1)
            else:
                lang, code = header_and_body.strip(), body
            lang = lang.strip().lower()
            if lang == "html":
                html_code = code
            elif lang == "css":
                css_code = code
            elif lang in ("javascript", "js"):
                js_code = code

        # Fallback: single-block variant like [HTML] + 'css\n...' + 'javascript\n...'
        if (css_code == "" or js_code == "") and html_code:
            # Try to split HTML block by explicit markers
            m = re.split(r'\ncss\s*\n', html_code, maxsplit=1, flags=re.IGNORECASE)
            if len(m) == 2:
                html_code, rest = m[0], m[1]
                n = re.split(r'\njavascript\s*\n', rest, maxsplit=1, flags=re.IGNORECASE)
                css_code = n[0].strip()
                js_code = (n[1].strip() if len(n) == 2 else "")

        return html_code.strip(), css_code.strip(), js_code.strip()

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Extract the first {...} JSON block.
        """
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        return m.group(0) if m else "{}"

    def _ensure_section_ids(self, html: str):
        """
        Ensure major sections are wrapped with stable IDs for targeted edits.
        Returns (updated_html, selectors_list)
        """
        if not html:
            return html, []

        selectors = []
        lines = html.splitlines()
        out = []
        section_open = False
        section_id = None

        header_re = re.compile(r"<h([1-4])([^>]*)>(.*?)</h\1>", flags=re.IGNORECASE)
        id_re = re.compile(r'id\s*=\s*"([^"]+)"', flags=re.IGNORECASE)

        def open_section(sec_id):
            return f'<section data-section-id="{sec_id}" id="{sec_id}">'

        for line in lines:
            h = header_re.search(line)
            if h:
                if section_open:
                    out.append("</section>")
                    section_open = False

                attrs = h.group(2) or ""
                text = re.sub("<.*?>", "", h.group(3)).strip()
                existing_id = id_re.search(attrs)
                if existing_id:
                    section_id = existing_id.group(1)
                else:
                    section_id = f"sec-{uuid.uuid4().hex[:8]}"
                    line = line.replace(h.group(0),
                        f'<h{h.group(1)} id="{section_id}"{attrs}>{h.group(3)}</h{h.group(1)}>' )

                selectors.append(f"#{section_id}")
                out.append(open_section(section_id))
                out.append(line)
                section_open = True
            else:
                out.append(line)

        if section_open:
            out.append("</section>")

        updated_html = "\n".join(out)
        return updated_html, selectors

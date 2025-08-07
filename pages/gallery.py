import streamlit as st

def run():
    st.set_page_config(page_title="Gallery - AI Website Builder", page_icon="🖼️")

    st.title("Website Gallery")
    st.markdown("Explore websites created with AI Website Builder")

    # Sample gallery items
    gallery_items = [
        {
            "title": "Portfolio Website",
            "description": "A modern portfolio website for a photographer",
            "image": "https://via.placeholder.com/300x200?text=Portfolio+Website"
        },
        {
            "title": "E-commerce Store",
            "description": "A sleek e-commerce website for a fashion brand",
            "image": "https://via.placeholder.com/300x200?text=E-commerce+Store"
        },
        {
            "title": "Restaurant Website",
            "description": "An elegant website for a fine dining restaurant",
            "image": "https://via.placeholder.com/300x200?text=Restaurant+Website"
        },
        {
            "title": "Tech Blog",
            "description": "A clean and modern tech blog",
            "image": "https://via.placeholder.com/300x200?text=Tech+Blog"
        }
    ]

    # Display gallery in a grid
    cols = st.columns(2)
    for i, item in enumerate(gallery_items):
        col = cols[i % 2]
        with col:
            st.image(item["image"])
            st.subheader(item["title"])
            st.markdown(item["description"])
            if st.button("Use Template", key=f"btn_{i}"):
                st.session_state.template = item["title"]
                # st.switch_page("app.py")

# Call the function when the page is run directly
if __name__ == "__main__":
    run()
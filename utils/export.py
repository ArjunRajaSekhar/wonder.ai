import zipfile
import io
import os

def export_website(generated_code, format="HTML Files"):
    """
    Export the generated website in the specified format
    """
    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        if format == "HTML Files":
            # Add HTML file
            zip_file.writestr("index.html", generated_code['html'])
            
            # Add CSS file
            zip_file.writestr("style.css", generated_code['css'])
            
            # Add JS file
            zip_file.writestr("script.js", generated_code['js'])
            
            # Add README
            readme = """# Your Generated Website

This website was generated using AI Website Builder.

## Files
- index.html: Main HTML file
- style.css: Stylesheet
- script.js: JavaScript code

## How to use
1. Open index.html in your web browser
2. Customize as needed
3. Deploy to any web server
"""
            zip_file.writestr("README.md", readme)
            
        elif format == "React Project":
            # Create a basic React project structure
            zip_file.writestr("package.json", """
{
  "name": "generated-website",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "4.0.3"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
""")
            
            # Create src directory
            zip_file.writestr("src/App.js", f"""
import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      {generated_code['html']}
    </div>
  );
}}

export default App;
""")
            
            zip_file.writestr("src/App.css", generated_code['css'])
            zip_file.writestr("src/index.js", """
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
""")
            
            zip_file.writestr("src/index.css", """
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
""")
            
            zip_file.writestr("public/index.html", """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Generated Website</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
""")
            
        elif format == "Vue Project":
            # Create a basic Vue project structure
            zip_file.writestr("package.json", """
{
  "name": "generated-website",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint"
  },
  "dependencies": {
    "core-js": "^3.6.5",
    "vue": "^3.0.0"
  },
  "devDependencies": {
    "@vue/cli-plugin-babel": "~4.5.0",
    "@vue/cli-plugin-eslint": "~4.5.0",
    "@vue/cli-service": "~4.5.0",
    "babel-eslint": "^10.1.0",
    "eslint": "^6.7.2",
    "eslint-plugin-vue": "^7.0.0"
  }
}
""")
            
            zip_file.writestr("src/App.vue", f"""
<template>
  <div id="app">
    {generated_code['html']}
  </div>
</template>

<script>
export default {{
  name: 'App',
}}
</script>

<style>
{generated_code['css']}
</style>
""")
            
            zip_file.writestr("src/main.js", """
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
""")
            
            zip_file.writestr("public/index.html", """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Generated Website</title>
  </head>
  <body>
    <noscript>
      <strong>We're sorry but this app doesn't work properly without JavaScript enabled. Please enable it to continue.</strong>
    </noscript>
    <div id="app"></div>
    <!-- built files will be auto injected -->
  </body>
</html>
""")
    
    zip_buffer.seek(0)
    return zip_buffer
import http.server
import socketserver
import json
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
try:
    from google import genai
    client = genai.Client()
    HAS_GEMINI = True
except Exception as e:
    HAS_GEMINI = False
    print(f"Warning: Gemini AI not configured properly. {e}")

try:
    import groq
    groq_client = groq.Groq()
    HAS_GROQ = True
except Exception as e:
    HAS_GROQ = False
    print(f"Warning: Groq AI not configured properly. {e}")

# Pre-load context
CONTEXT = ""
try:
    with open(os.path.join(os.path.dirname(__file__), 'output', 'discovery_report.md'), 'r', encoding='utf-8') as f:
        CONTEXT = f.read()
except Exception as e:
    print("Warning: Could not read context file.", e)

PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(__file__), "site")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/ask':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            question = data.get("question", "")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_cors_headers()
            self.end_headers()

            if not HAS_GEMINI and not HAS_GROQ:
                response = {"error": "AI client not initialized. Check GEMINI_API_KEY or GROQ_API_KEY in .env"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            try:
                # Ask Gemini
                system_prompt = f"You are the AI Discovery Engine for a Google Photos retrieval analysis project. Answer the user's question using ONLY the following generated discovery report context. If the answer is not in the context, say so. Do not invent information. IMPORTANT FORMATTING RULES: 1) Do not include any record counts or numbers of records in your answers. 2) Provide your answer in plain text without using markdown special characters like asterisks, hashtags, or underscores.\n\nContext:\n{CONTEXT}"
                if HAS_GEMINI:
                    try:
                        resp = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=question,
                            config=genai.types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.2,
                            ),
                        )
                        response = {"answer": resp.text}
                    except Exception as e:
                        if HAS_GROQ:
                            print(f"Gemini failed ({e}), falling back to Groq...")
                            # Fallback to Groq with truncated context to fit TPM limits
                            truncated_prompt = system_prompt[:25000]
                            resp = groq_client.chat.completions.create(
                                model="openai/gpt-oss-120b",
                                messages=[
                                    {"role": "system", "content": truncated_prompt},
                                    {"role": "user", "content": question}
                                ],
                                temperature=0.2
                            )
                            response = {"answer": resp.choices[0].message.content}
                        else:
                            response = {"error": str(e)}
                else:
                    # Fallback to Groq if Gemini wasn't initialized at all
                    truncated_prompt = system_prompt[:25000]
                    resp = groq_client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {"role": "system", "content": truncated_prompt},
                            {"role": "user", "content": question}
                        ],
                        temperature=0.2
                    )
                    response = {"answer": resp.choices[0].message.content}
            except Exception as e:
                response = {"error": str(e)}

            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

if __name__ == '__main__':
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

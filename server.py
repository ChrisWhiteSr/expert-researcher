from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from urllib.parse import parse_qs, urlparse
import openai
import logging
from dotenv import load_dotenv
import mimetypes
import traceback

# Load environment variables from .env file
load_dotenv()

# Set up logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set your OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API Key configured: {'Yes' if openai.api_key else 'No'}")

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Serve static files
            if self.path == '/':
                self.path = '/index.html'
            
            filepath = os.path.join(os.getcwd(), self.path.lstrip('/'))
            logger.info(f"Attempting to serve: {filepath}")
            
            if os.path.exists(filepath) and os.path.isfile(filepath):
                content_type, _ = mimetypes.guess_type(filepath)
                if content_type is None:
                    content_type = 'application/octet-stream'

                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                logger.info(f"Successfully served: {filepath}")
            else:
                logger.error(f"File not found: {filepath}")
                self.send_error(404, "File not found")
        except Exception as e:
            logger.error(f"GET request error: {str(e)}")
            logger.error(traceback.format_exc())
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            logger.info("Handled OPTIONS request")
        except Exception as e:
            logger.error(f"OPTIONS request error: {str(e)}")
            logger.error(traceback.format_exc())

    def do_POST(self):
        try:
            logger.info(f"Received POST request to path: {self.path}")
            
            # Check if this is the suggest endpoint
            if self.path != '/suggest':
                logger.error(f"Invalid endpoint requested: {self.path}")
                self.send_error(404, "Endpoint not found")
                return

            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            logger.info(f"Content length: {content_length}")

            # Read post data
            post_data = self.rfile.read(content_length)
            logger.info(f"Received data: {post_data.decode('utf-8')}")
            
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            query = data.get('query', '')
            logger.info(f"Processing query: {query}")

            if not query:
                logger.error("Empty query received")
                self.send_error(400, "Query parameter is required")
                return

            # Verify OpenAI API key is set
            if not openai.api_key:
                logger.error("OpenAI API key not configured")
                raise ValueError("OpenAI API key not configured")

            # Call OpenAI API
            logger.info("Calling OpenAI API...")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research assistant helping to refine academic search queries. Provide specific, targeted suggestions that would yield better academic search results. Focus on technical terminology and key concepts."
                    },
                    {
                        "role": "user",
                        "content": f'Please suggest a refined academic search query for: "{query}". Return only the suggested query without explanation.'
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )

            suggestion = response.choices[0].message.content.strip()
            logger.info(f"Got suggestion: {suggestion}")

            # Send response
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response_data = json.dumps({"suggestion": suggestion})
            self.wfile.write(response_data.encode('utf-8'))
            logger.info("Successfully sent response")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(traceback.format_exc())
            self.send_error(400, f"Invalid JSON: {str(e)}")
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            logger.error(traceback.format_exc())
            self.send_error(500, f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            self.send_error(500, str(e))

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

def run():
    try:
        port = int(os.getenv('PORT', 3000))
        server_address = ('', port)
        httpd = HTTPServer(server_address, RequestHandler)
        logger.info(f'Server running on port {port}')
        logger.info(f'OpenAI API key configured: {bool(openai.api_key)}')
        logger.info('Server ready to handle requests')
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    run()

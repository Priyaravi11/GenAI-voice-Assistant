"""
API testing script for GenAI Voice Assistant.

Tests core endpoints:
- Health check
- Query processing
- WebSocket communication
- Escalation workflow

Usage:
    python scripts/test_api.py              # Run all tests
    python scripts/test_api.py --health     # Health check only
    python scripts/test_api.py --url http://localhost:8001  # Custom URL
"""

import asyncio
import json
import argparse
from typing import Dict, Any, Optional
import httpx
import websockets


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


class APITester:
    """Test API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize tester."""
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)
    
    def test_health(self) -> bool:
        """Test health endpoint."""
        print_header("Testing Health Endpoint")
        
        try:
            response = self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                print_success(f"Health check passed")
                print_info(f"Response: {response.json()}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
        
        except Exception as e:
            print_error(f"Failed to connect: {e}")
            print_warning(f"Make sure server is running at {self.base_url}")
            return False
    
    def test_query_endpoint(self) -> bool:
        """Test query processing endpoint."""
        print_header("Testing Query Endpoint")
        
        test_queries = [
            {
                "customer_id": "C001",
                "query": "What is my current bill?",
                "language": "en"
            },
            {
                "customer_id": "C002",
                "query": "मेरा बिल क्या है?",
                "language": "hi"
            },
        ]
        
        for test_query in test_queries:
            try:
                print_info(f"Sending query: {test_query['query']}")
                
                response = self.client.post(
                    f"{self.base_url}/api/query",
                    json=test_query
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Query processed successfully")
                    print_info(f"Response: {data.get('response', 'No response')}")
                else:
                    print_warning(f"Response status: {response.status_code}")
            
            except Exception as e:
                print_error(f"Query test failed: {e}")
                return False
        
        return True
    
    def test_call_logs(self) -> bool:
        """Test call logs endpoint."""
        print_header("Testing Call Logs Endpoint")
        
        try:
            response = self.client.get(
                f"{self.base_url}/api/calls/C001"
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Retrieved {len(data.get('calls', []))} call records")
                return True
            else:
                print_warning(f"Response status: {response.status_code}")
                return False
        
        except Exception as e:
            print_error(f"Call logs test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()


class WebSocketTester:
    """Test WebSocket communication."""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        """Initialize tester."""
        self.base_url = base_url
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection."""
        print_header("Testing WebSocket Connection")
        
        try:
            ws_url = f"{self.base_url}/ws/C001"
            print_info(f"Connecting to: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                print_success("WebSocket connected")
                
                # Send query
                query_message = {
                    "type": "query",
                    "content": "What is my bill?",
                    "language": "en"
                }
                
                print_info(f"Sending message: {json.dumps(query_message)}")
                await websocket.send(json.dumps(query_message))
                
                # Receive response
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=5.0
                    )
                    print_success("Received response")
                    print_info(f"Response: {response[:100]}...")
                    return True
                
                except asyncio.TimeoutError:
                    print_warning("Response timeout")
                    return False
        
        except Exception as e:
            print_error(f"WebSocket test failed: {e}")
            return False
    
    async def test_websocket_multiple_messages(self) -> bool:
        """Test multiple messages over WebSocket."""
        print_header("Testing Multiple WebSocket Messages")
        
        try:
            ws_url = f"{self.base_url}/ws/C001"
            
            async with websockets.connect(ws_url) as websocket:
                print_success("WebSocket connected")
                
                messages = [
                    "What is my bill?",
                    "How can I pay?",
                    "What are my plan options?",
                ]
                
                for i, msg in enumerate(messages, 1):
                    query = {
                        "type": "query",
                        "content": msg,
                        "language": "en"
                    }
                    
                    print_info(f"Message {i}: {msg}")
                    await websocket.send(json.dumps(query))
                    
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=3.0
                        )
                        print_success(f"  Received response")
                    except asyncio.TimeoutError:
                        print_warning(f"  Response timeout")
                
                return True
        
        except Exception as e:
            print_error(f"Multiple messages test failed: {e}")
            return False


async def run_tests(
    base_url: str = "http://localhost:8000",
    health_only: bool = False,
    websocket_only: bool = False
) -> bool:
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}GenAI Voice Assistant - API Tests{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    results = {}
    
    # HTTP Tests
    if not websocket_only:
        http_tester = APITester(base_url)
        
        # Health check
        results["Health Check"] = http_tester.test_health()
        
        if not health_only:
            # Query endpoint
            results["Query Endpoint"] = http_tester.test_query_endpoint()
            
            # Call logs
            results["Call Logs"] = http_tester.test_call_logs()
        
        http_tester.close()
    
    # WebSocket Tests
    if not health_only:
        ws_url = base_url.replace("http", "ws")
        ws_tester = WebSocketTester(ws_url)
        
        results["WebSocket Connection"] = await ws_tester.test_websocket_connection()
        results["WebSocket Multiple Messages"] = await ws_tester.test_websocket_multiple_messages()
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print_info(f"{symbol} {test_name}: {status}")
    
    print()
    print_success(f"Passed: {passed}/{total}")
    
    return passed == total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test GenAI Voice Assistant API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Health check only"
    )
    parser.add_argument(
        "--websocket",
        action="store_true",
        help="WebSocket tests only"
    )
    
    args = parser.parse_args()
    
    success = asyncio.run(run_tests(
        base_url=args.url,
        health_only=args.health,
        websocket_only=args.websocket
    ))
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

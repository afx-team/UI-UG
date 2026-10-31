"""Run a UI-UG 2 instruction against an OpenAI-compatible vLLM server."""
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image", help="Optional local screenshot or URL")
    parser.add_argument("--model", default=os.getenv("SERVED_MODEL_NAME", "uiug2"))
    parser.add_argument("--api-base", default=os.getenv("VLLM_API_BASE", "http://127.0.0.1:8000/v1"))
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()
    from utils.vllm_chat import VLLMChatInference

    client = VLLMChatInference(api_base=args.api_base, max_tokens=args.max_tokens)
    method = client.chat_with_image_stream if args.stream else client.chat_with_image
    print(method(args.model, args.prompt, args.image))


if __name__ == "__main__":
    main()

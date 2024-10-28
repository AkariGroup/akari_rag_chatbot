import argparse
import time

from lib.chat import ChatStream
from lib.prompt_creator import system_prompt_creator
from lib.weaviate_rag_retriever import WeaviateRagRetriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model",
        nargs="+",
        type=str,
        default=["azure_gpt-4o"],
        help="Model name list",
    )
    parser.add_argument(
        "-c",
        "--collections",
        default="Test",
        type=str,
        help="Weaviate collection name",
    )
    args = parser.parse_args()
    chat_stream = ChatStream()
    retriever = WeaviateRagRetriever()
    messages_list = []
    for i in range(0, len(args.model)):
        messages_list.append([""])
    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        rag_start = time.time()
        response = retriever.hybrid_search(text=text, limit=3, alpha=0.75, rerank=False,collection_name=args.collections)
        print(f"search time: {time.time() - rag_start:.2f} [s]")
        contexts = ""
        """
            print(f"distance: {p.metadata.distance}")
            print(f"certainty: {p.metadata.certainty}")
            print(f"score: {p.metadata.score}")
            print(f"explain_score: {p.metadata.explain_score}")
            print(f"source: {p.properties['source']}")
            print(f"content: {p.properties['content']}")
            print()
        """
        for p in response.objects:
            contexts += p.properties["content"]
        system_prompt = system_prompt_creator(prev_context="", context=contexts)
        for i, model in enumerate(args.model):
            messages_list[i][0] = chat_stream.create_message(
                system_prompt, role="system"
            )
            messages_list[i].append(chat_stream.create_message(text, role="user"))
            response = ""
            start = time.time()
            is_first = True
            output_delay = 0.0
            for sentence in chat_stream.chat(
                messages_list[i], model=model, temperature=0.2
            ):
                response += sentence
                print(sentence, end="", flush=True)
                if is_first:
                    output_delay = time.time() - start
                    is_first = False
            # chatGPTの返答をassistantメッセージとして追加
            messages_list[i].append(
                chat_stream.create_message(response, role="assistant")
            )
            interval = time.time() - start
            print("")
            print("-------------------------")
            print(f"delay: {output_delay:.2f} [s]  total_time: {interval:.2f} [s]")
            print("")


if __name__ == "__main__":
    main()

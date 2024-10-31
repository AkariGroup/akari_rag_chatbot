import argparse

from lib.weaviate_rag_controller import WeaviateRagController


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--collections",
        default="Test",
        type=str,
        help="Weaviate collection name",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        help="Source name",
    )
    parser.add_argument(
        "-s",
        "--show_all",
        action="store_true",
        help="Show all content in objects",
    )
    args = parser.parse_args()
    weaviate_controller = WeaviateRagController()
    if args.name is not None:
        list = weaviate_controller.get_objects_by_source(source=args.name, collection_name=args.collections)
    else:
        list = weaviate_controller.get_objects(collection_name=args.collections)
    list.sort(key=lambda item: (item.properties['source'], item.properties['chunk_index']))
    for item in list:
        print(f"source: {item.properties['source']}")
        print(f"uuid: {item.uuid}")
        print(f"date: {item.properties['date']}")
        print(f"chunk_index: {item.properties['chunk_index']}")
        if args.show_all:
            print(f"content: {item.properties['content']}")
        else:
            print(f"content: {item.properties['content'][:60]}...")
        print("====================================")
    print(f"Total chunks: {len(list)}")


if __name__ == "__main__":
    main()

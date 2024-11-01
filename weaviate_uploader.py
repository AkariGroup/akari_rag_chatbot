import argparse
import os

from lib.weaviate_rag_controller import WeaviateRagController


# 使用例
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, help="path to load text files")
    parser.add_argument(
        "-c",
        "--collection",
        type=str,
        help="Weaviate collection",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove the collection before uploading",
    )
    args = parser.parse_args()
    # アップローダーの初期化
    weaviate_controller = WeaviateRagController()
    if args.collection is None:
        print(
            "Collection name is not available. Please specify collection name with '-c {collection_name}'."
        )
        print(f"Current collections: {weaviate_controller.get_collections()}")
    if args.remove:
        weaviate_controller.remove_collection(collection_name=args.collection)
    file_paths = []
    if args.path is None:
        print("Path is not available")
        return
    if os.path.isdir(args.path):
        file_paths = [
            os.path.join(root, file)
            for root, dirs, files in os.walk(args.path)
            for file in files
        ]
    else:
        file_paths.append(args.path)
    if len(file_paths) > 0:
        results = weaviate_controller.upload_files(
            collection_name=args.collection, file_paths=file_paths
        )
    else:
        print(f"No files found in {args.path}")
        return


if __name__ == "__main__":
    main()

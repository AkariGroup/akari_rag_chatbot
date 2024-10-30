import argparse
import os

from lib.weaviate_rag_uploader import WeaviateRagUploader


# 使用例
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--weaviate_url",
        type=str,
        default="http://localhost:8080",
        help="Weaviate URL",
    )
    parser.add_argument(
        "-p", "--path", type=str, default="created_data", help="path to load text files"
    )
    parser.add_argument(
        "-c",
        "--collection",
        type=str,
        default="Test",
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
    uploader = WeaviateRagUploader(
        weaviate_url=args.weaviate_url,
        chunk_size=1000,
        chunk_overlap=200,
        collection_name=args.collection,
        remove_collection=args.remove,
    )
    file_paths = []
    if args.path is None:
        print("Path is not available")
    for root, dirs, files in os.walk(args.path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    if len(file_paths) > 0:
        results = uploader.upload_files(file_paths=file_paths)
    else:
        print(f"No files found in {args.path}")
        return


if __name__ == "__main__":
    main()

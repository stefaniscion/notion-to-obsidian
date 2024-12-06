import os
import re
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import unquote


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Converts Notion notes to Obsidian")
    parser.add_argument(
        "-s",
        "--source",
        help="Path to the Notion notes",
        default="./input/",
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="Path to the Obsidian vault",
        default="./output/",
    )
    return parser


def format_tags(match):
    tags = match.group(1)
    tags = tags.split(", ")
    tags = [tag.lower() for tag in tags]
    tags = [tag.replace(" ", "-") for tag in tags]
    tags = [tag.replace("/", "-") for tag in tags]
    content = "Tags:\n"
    for tag in tags:
        content = content + f"- {tag}\n"
    return "---\n" + content + "---"


def elaborate_headers(content: str) -> str:
    # delete first two lines
    content = content.split("\n", 2)[2]
    content = re.sub(r"Verificato:.*", "", content)
    content = re.sub(r"Proprietario:.*", "", content)
    content = re.sub(r"Etichette: (.*)", format_tags, content)
    content = re.sub(r"^\s*\n", "", content)
    return content


def elaborate_links(match: re.Match):
    text = match.group(1)
    if text.startswith("http"):
        return f"[{text}]({match.group(2)})"
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # removes bold
    return f"[[{text}]]"


def replace_links(content: str) -> str:
    return re.sub(r'\[(.*?)\]\((.*?)\s?(?:"(.*?)")?\)', elaborate_links, content)


def decode_url_from_link(match: re.Match):
    url = match.group(2)
    url = unquote(url)
    return f"![[img/{url}]]"


def replace_images(content: str) -> str:
    return re.sub(r'!\[(.*?)\]\((.*?)\s?(?:"(.*?)")?\)', decode_url_from_link, content)


def remove_hex_from_filename(filename: str) -> str:
    return re.sub(r"\s[0-9a-f]{32}", "", filename)


def generate_blockquote(match: re.Match) -> str:
    text = match.group(1)
    # add a > to the beginning of each line
    text = re.sub(r"^", "> ", text, flags=re.MULTILINE)
    return f"{text}"


def replace_asides_with_quotes(content: str) -> str:
    # replace multiline <aside>(.*)</aside> with blockquote
    return re.sub(
        r"<aside>(.*?)</aside>", generate_blockquote, content, flags=re.DOTALL
    )


parser = create_parser()
args = parser.parse_args()
source = Path(args.source)
destination = Path(args.destination)

for root, dirs, files in os.walk(source):
    for file in files:
        if file.endswith(".md"):
            new_file_name = remove_hex_from_filename(file)
            with open(os.path.join(root, file), "r") as f:
                content = f.read()
                content = elaborate_headers(content)
                content = replace_images(content)
                content = replace_links(content)
                content = replace_asides_with_quotes(content)
            with open(os.path.join(destination, new_file_name), "w") as f:
                f.write(content)
                print(f"[i] writing {new_file_name}")
        else:
            print(f"[i] copying {file}")
            # copy image as is
            os.makedirs(os.path.join(destination, "img"), exist_ok=True)
            os.system(
                f"cp \"{os.path.join(root, file)}\" \"{os.path.join(destination, 'img')}\""
            )

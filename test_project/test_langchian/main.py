import argparse
import json

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv(find_dotenv())


def invoke(prompt, input, settings):
    prompt_template = PromptTemplate(template=prompt)
    llm = ChatOpenAI(model=settings['model'])
    chain = prompt_template | llm | StrOutputParser()
    print(chain.invoke({'input': input}))


def str_to_dict(s):
    try:
        d = json.loads(s)
        if isinstance(d, dict):
            return d
        raise argparse.ArgumentTypeError("无效的字典值")
    except (ValueError, SyntaxError):
        raise argparse.ArgumentTypeError("无效的字典值")


def main():
    # 创建解析器
    parser = argparse.ArgumentParser(description='处理命令行参数')

    # 添加参数
    parser.add_argument('-p', '--prompt', type=str, help='提示信息')
    parser.add_argument('-i', '--input', type=str, help='输入信息')
    parser.add_argument('-s', '--settings', type=str_to_dict,
                        help='设置信息，例如: {"key": "value"}')

    # 解析参数
    args = parser.parse_args()

    # 输出参数值
    invoke(args.prompt, args.input, args.settings)


if __name__ == '__main__':
    main()

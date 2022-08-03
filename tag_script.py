import argparse
from source.tag_scores import ScoreTagger

if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='Get path for scores to tag.')
    parser.add_argument('path', type=str)

    args = parser.parse_args()
    

    print(f'tagging scores: {args.path}')
    st = ScoreTagger(args.path)
    st.run()
import os
import datetime
import asyncio
import pstats
import cProfile

from icecream import ic


def debug_ic(*args):
    """icecream 디버깅 함수

    Args:
        *args: 디버깅할 변수/값
    """
    if os.getenv("DEBUG") == "true":
        return ic(*args)
    else:
        return None


def make_dir(path):
    """디렉토리 생성 함수

    Args:
        path (str): 생성할 디렉토리 경로
    """
    if not os.path.exists(path):
        os.makedirs(path)
        msg = f'Directory created: {path}'
        print(msg)
        return msg
    else:
        msg = f'Directory already exists: {path}'
        print(msg)
        return msg


def get_current_datetime():
    """현재 시간을 반환하는 함수

    Returns:
        str: 현재 시간 문자열
    """
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def format_error_message(error_dict):
    """딕셔너리 형태의 오류 정보에서 오류 메시지를 생성하는 함수

    Args:
        error_dict (dict): 오류 정보를 담고 있는 딕셔너리.
                           예: {'type': 'GPU_OOM', 'message': 'GPU memory is out of memory'}

    Returns:
        str: 포맷된 오류 메시지
    """
    error_type = error_dict.get("type", "Unknown Error")
    error_message = error_dict.get("message", "")
    return f"[{error_type}] {error_message}"


def snake_to_camel(word):
    # 언더스코어가 없으면 원본 문자열 반환
    if '_' not in word:
        return word
    # 언더스코어가 있는 경우 변환 수행
    words = word.split('_')
    return words[0].lower() + ''.join(x.capitalize() for x in words[1:])


def profile_async_func(func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    result = asyncio.run(func(*args, **kwargs))
    pr.disable()
    ps = pstats.Stats(pr).sort_stats('cumulative')
    ps.print_stats()
    return result


def profile_func(func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()
    ps = pstats.Stats(pr).sort_stats('cumulative')
    ps.print_stats()
    return result

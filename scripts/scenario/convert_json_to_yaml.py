#!/usr/bin/env python3
"""
JSON 시나리오 파일을 YAML 형식으로 변환하는 유틸리티

사용법:
    # 단일 파일 변환
    python3 convert_json_to_yaml.py scenario.json
    
    # 디렉토리 전체 변환 (재귀적)
    python3 convert_json_to_yaml.py /path/to/scenario/directory
    
    # 원본 JSON 파일 삭제 옵션
    python3 convert_json_to_yaml.py /path/to/directory --delete-json
"""

import json
import yaml
import argparse
import os
from pathlib import Path
from typing import Dict, Any


def clean_dict(data: Any) -> Any:
    """None 값과 빈 dict/list를 재귀적으로 제거"""
    if isinstance(data, dict):
        return {k: clean_dict(v) for k, v in data.items() if v is not None and v != {} and v != []}
    elif isinstance(data, list):
        return [clean_dict(item) for item in data]
    else:
        return data


def convert_json_to_yaml(json_file: Path, delete_json: bool = False) -> bool:
    """JSON 파일을 YAML로 변환
    
    Args:
        json_file: 변환할 JSON 파일 경로
        delete_json: 변환 후 원본 JSON 파일 삭제 여부
        
    Returns:
        변환 성공 여부
    """
    try:
        # JSON 읽기
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # None 값 정리
        data = clean_dict(data)
        
        # YAML 파일명 생성
        yaml_file = json_file.with_suffix('.yaml')
        
        # YAML로 저장
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        
        print(f"✓ {json_file.name} → {yaml_file.name}")
        
        # 원본 JSON 삭제 (옵션)
        if delete_json:
            json_file.unlink()
            print(f"  🗑️  {json_file.name} 삭제됨")
        
        return True
        
    except Exception as e:
        print(f"✗ {json_file.name}: {str(e)}")
        return False


def convert_directory(directory: Path, delete_json: bool = False) -> tuple[int, int]:
    """디렉토리의 모든 JSON 파일을 재귀적으로 변환
    
    Args:
        directory: 변환할 디렉토리 경로
        delete_json: 변환 후 원본 JSON 파일 삭제 여부
        
    Returns:
        (성공 개수, 실패 개수) 튜플
    """
    success_count = 0
    fail_count = 0
    
    # 재귀적으로 모든 JSON 파일 찾기
    for json_file in directory.rglob("*.json"):
        # hosts.json, environment 파일 등은 제외
        if json_file.parent.name in ['config', 'env']:
            continue
            
        if convert_json_to_yaml(json_file, delete_json):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description='JSON 시나리오 파일을 YAML 형식으로 변환',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 파일 변환
  python3 convert_json_to_yaml.py scenario.json
  
  # 디렉토리 전체 변환
  python3 convert_json_to_yaml.py /path/to/scenario/directory
  
  # 원본 JSON 파일 삭제
  python3 convert_json_to_yaml.py /path/to/directory --delete-json
        """
    )
    
    parser.add_argument(
        'path',
        help='JSON 파일 또는 디렉토리 경로'
    )
    
    parser.add_argument(
        '--delete-json',
        action='store_true',
        help='변환 후 원본 JSON 파일 삭제'
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {args.path}")
        return
    
    print(f"\n🔄 JSON → YAML 변환 시작")
    print(f"📂 대상: {args.path}")
    if args.delete_json:
        print(f"⚠️  변환 후 원본 JSON 파일을 삭제합니다")
    print()
    
    if path.is_file():
        if path.suffix != '.json':
            print("❌ JSON 파일이 아닙니다")
            return
        
        if convert_json_to_yaml(path, args.delete_json):
            print(f"\n✅ 변환 완료!")
        else:
            print(f"\n❌ 변환 실패")
    
    elif path.is_dir():
        success, fail = convert_directory(path, args.delete_json)
        
        print(f"\n{'='*50}")
        print(f"✅ 변환 완료: {success}개 파일")
        if fail > 0:
            print(f"❌ 실패: {fail}개 파일")
        print(f"{'='*50}")
    
    else:
        print("❌ 유효하지 않은 경로입니다")


if __name__ == '__main__':
    main()

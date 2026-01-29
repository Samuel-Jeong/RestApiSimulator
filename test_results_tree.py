#!/usr/bin/env python3
"""
테스트 결과 트리 구조 테스트 스크립트
"""

from app.core.project_manager import ProjectManager
import json

def test_results_tree():
    """결과 트리 구조 테스트"""
    pm = ProjectManager()
    
    # 프로젝트 목록 확인
    projects = pm.list_projects()
    print(f"✅ 발견된 프로젝트: {len(projects)}개")
    
    if not projects:
        print("❌ 프로젝트가 없습니다.")
        return
    
    # 모든 프로젝트의 결과 확인
    for project_name in projects:
        results_list = pm.list_results(project_name)
        if results_list:
            print(f"\n📁 프로젝트: {project_name} ({len(results_list)}개 결과)")
            print("="*60)
            
            try:
                # 결과 트리 구조 가져오기
                results_tree = pm.get_results_tree(project_name)
                
                # 트리 구조 출력
                print("\n🌳 트리 구조:")
                print("-"*60)
                
                def print_tree(node, prefix="", is_last=True, counter=[0]):
                    """트리 출력"""
                    if node['type'] == 'folder':
                        connector = "└── " if is_last else "├── "
                        if node['path'] == '':
                            # 루트
                            print(f"\n{node['name']}/")
                        else:
                            icon = "📅 " if node['name'].isdigit() and len(node['name']) == 8 else "📁 "
                            label = node['name']
                            if node['name'] == 'scenarios':
                                label = f"{node['name']} (Scenario Tests)"
                            elif node['name'] == 'loadtests':
                                label = f"{node['name']} (Load Tests)"
                            print(f"{prefix}{connector}{icon}{label}/")
                        
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        children = node.get('children', [])
                        for i, child in enumerate(children):
                            print_tree(child, new_prefix, i == len(children) - 1, counter)
                    
                    elif node['type'] == 'file':
                        connector = "└── " if is_last else "├── "
                        counter[0] += 1
                        
                        # 아이콘
                        if node.get('test_type') == 'scenario':
                            icon = "📄 "
                        elif node.get('test_type') == 'loadtest':
                            icon = "⚡ "
                        else:
                            icon = "📋 "
                        
                        # 파일 크기
                        size_kb = node.get('size', 0) / 1024
                        size_str = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
                        
                        # 이름 (최대 50자)
                        name = node['name']
                        if len(name) > 50:
                            name = name[:47] + "..."
                        
                        print(f"{prefix}{connector}[{counter[0]:2d}] {icon}{name} ({size_str})")
                
                print_tree(results_tree)
                
                print("\n"+"="*60)
                print("✅ 트리 구조 테스트 완료")
                
                # 첫 번째 결과만 테스트하고 종료
                break
                
            except Exception as e:
                print(f"❌ 에러 발생: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("\n❌ 결과 파일이 있는 프로젝트를 찾을 수 없습니다.")

if __name__ == '__main__':
    test_results_tree()

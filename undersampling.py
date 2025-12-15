import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# 1. 엑셀 파일 불러오기
# (방금 저장한 파일명을 적어주세요)
file_path = 'zigzag_balanced_data.xlsx'
df = pd.read_excel(file_path)

# -------------------------------------------------------
# 실제 라벨 컬럼명으로 수정해주세요 (예: 'label', 'score' 등)
target_column = 'label'
# -------------------------------------------------------

# 2. 한글 폰트 설정 (그래프에서 한글이 깨지지 않게 함)
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin': # Mac
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

# 3. 데이터 개수 세기
counts = df[target_column].value_counts().sort_index()

# 4. 그래프 그리기
plt.figure(figsize=(8, 6))

# 막대 색상 설정 (0: 빨강/부정, 1: 파랑/긍정)
colors = ['#ff6b6b', '#4dabf7']

# 바 차트 생성
bars = plt.bar(counts.index.astype(str), counts.values, color=colors, width=0.5)

# 5. 막대 위에 숫자 표시하기
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, height, f'{int(height)}개',
             ha='center', va='bottom', fontsize=12, fontweight='bold')

# 6. 그래프 꾸미기
plt.title(f'최종 데이터셋 라벨 분포 (총 {len(df)}개)', fontsize=15)
plt.xlabel('라벨 (0:부정, 1:긍정)', fontsize=12)
plt.ylabel('리뷰 개수', fontsize=12)
plt.xticks(ticks=[0, 1], labels=['부정 (0)', '긍정 (1)']) # X축 이름 변경

plt.show()
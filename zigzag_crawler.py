import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# ==========================================
# [설정] 지그재그 상품 URL 리스트
TARGET_URLS = [
    # 슬로우앤드 (슬랙스: 900개)
    "https://zigzag.kr/catalog/products/136095576",

]

# 목표 리뷰 수
REVIEWS_PER_PRODUCT = 1000


# ==========================================

def crawl_zigzag_product(driver, url, target_count):
    print(f"\n>> [지그재그 접속] {url}")
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))

        # ---------------------------------------------------------
        # 1. '리뷰' 탭 클릭
        # ---------------------------------------------------------
        if "review/list" not in url:
            print("   ㄴ 1. '리뷰' 탭 이동 중...")
            try:
                driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(1)

                review_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-custom-ta-key*='PDP_REVIEW_TAB']"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_tab)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", review_tab)
                time.sleep(2)
            except:
                print("      (탭 클릭 패스)")

            # ---------------------------------------------------------
            # 2. '리뷰 전체보기' 클릭 (포토 제외)
            # ---------------------------------------------------------
            print("   ㄴ 2. '리뷰 전체보기' 버튼 클릭 시도...")
            try:
                see_all_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(., '리뷰 전체보기') and not(contains(., '포토'))]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_all_btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", see_all_btn)
                print("      -> 클릭 성공! 리스트 로딩 중...")
                time.sleep(3)
            except:
                print("      (버튼 클릭 실패 또는 이미 진입함)")

        # ---------------------------------------------------------
        # 3. 데이터 수집 (멈춤 해결 로직 추가)
        # ---------------------------------------------------------
        print(f"   ㄴ 3. 데이터 수집 시작 (목표: {target_count}개)...")

        collected_reviews = []
        scroll_stuck_count = 0  # 데이터가 안 늘어나는 횟수 카운트
        prev_len = 0  # 직전 수집 개수

        while True:
            # 1) 스크롤 다운
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.0)

            # 2) "더보기" 버튼 클릭 (리뷰 카드 내부만)
            try:
                more_buttons = driver.find_elements(By.CSS_SELECTOR, "div[data-review-feed-index] p")
                valid_buttons = [btn for btn in more_buttons if btn.text.strip() == "더보기"]
                if valid_buttons:
                    driver.execute_script("arguments[0].forEach(function(btn) { btn.click(); });", valid_buttons)
                    time.sleep(0.5)
            except:
                pass

            # 3) 데이터 추출
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            review_cards = soup.find_all("div", attrs={"data-review-feed-index": True})

            for card in review_cards:
                try:
                    content_span = card.find("span", class_=lambda x: x and "ebrcgb90" in x)
                    if not content_span:
                        more_btn = card.find("p", text="더보기")
                        if more_btn: content_span = more_btn.parent

                    if content_span:
                        full_text = content_span.get_text(" ", strip=True).replace("더보기", "").strip()
                        if len(full_text) > 10:
                            reviews_item = {"url": url, "리뷰": full_text}

                            # 중복 체크 (리스트 대신 딕셔너리 키로 체크하면 더 빠름, 여기선 리스트 유지)
                            is_duplicate = False
                            for item in collected_reviews:
                                if item['리뷰'] == full_text:
                                    is_duplicate = True
                                    break
                            if not is_duplicate:
                                collected_reviews.append(reviews_item)
                except:
                    continue

            # 4) 현황 출력 및 멈춤 감지
            current_len = len(collected_reviews)
            print(f"      ... 현재 수집된 개수: {current_len}개")

            if current_len >= target_count:
                print("   ㄴ 목표 수량 달성!")
                break

            # ★★★ [핵심] 데이터가 안 늘어날 때 강력 대응 ★★★
            if current_len == prev_len:
                scroll_stuck_count += 1
                print(f"      ⚠️ 데이터 정체 중... ({scroll_stuck_count}/10)")

                if scroll_stuck_count >= 10:
                    print("   ㄴ 진짜 더 이상 데이터가 없습니다. 수집 종료.")
                    break

                # 정체되었을 때: 위로 많이 올렸다가 다시 내림 (새로고침 효과)
                # 300px이 아니라 1000px 정도 확 올려버립니다.
                driver.execute_script("window.scrollBy(0, -1000);")
                time.sleep(1.0)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3.0)  # 로딩 시간 더 줌
            else:
                scroll_stuck_count = 0  # 데이터 늘어났으면 카운트 초기화

            prev_len = current_len

        print(f"   ✅ 최종 수집 완료: {len(collected_reviews)}개")
        return collected_reviews

    except Exception as e:
        print(f"   ❌ 에러 발생: {e}")
        return []


def main():
    print(f">> 지그재그 크롤링 시작 (총 {len(TARGET_URLS)}개 상품)")
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")

    try:
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=142)
    except Exception as e:
        print(f"❌ 드라이버 오류: {e}")
        return

    try:
        for i, url in enumerate(TARGET_URLS):
            print(f"\n--- [{i + 1}/{len(TARGET_URLS)}] 번째 상품 ---")
            product_reviews = crawl_zigzag_product(driver, url, REVIEWS_PER_PRODUCT)

            if product_reviews:
                df = pd.DataFrame(product_reviews)
                df = df.drop_duplicates(subset=['리뷰'])

                try:
                    p_id = url.split('/')[-1]
                except:
                    p_id = f"product_{i}"
                filename = f"zigzag_review_{p_id}.xlsx"

                df.to_excel(filename, index=False)
                print(f"💾 저장 완료: {filename} ({len(df)}개)")
            else:
                print("⚠️ 수집된 데이터가 없습니다.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
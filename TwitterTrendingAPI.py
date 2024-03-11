import re
import numpy as np
from mysql import connector
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

user_data_path_ = "\\Default_Twitter_Trending"

trending_set = set()
final = []
final2 = []


def process_trending_data(trending_list):
    total_posts = 0
    count = 0

    for item in trending_list:
        match = re.search(r'(.+?)(\d+(\.\d+)?(,\d{3})*(\.\d+)?[KM]?)\s*posts?', item)
        if match:
            count += 1
            value = match.group(2).replace(',', '')  # Remove commas
            multiplier = 1
            if 'K' in value:  # 'K' multiplier present
                multiplier = 1000
            elif 'M' in value:  # 'M' multiplier present
                multiplier = 1000000
            value = float(value[:-1]) * multiplier  # Remove 'K' or 'M' and apply multiplier
            total_posts += value

    average_value = total_posts / count if count > 0 else 0

    trending_dict = {}

    for item in trending_list:
        match = re.search(r'(.+?)(\d+(\.\d+)?(,\d{3})*(\.\d+)?[KM]?)\s*posts?', item)
        key = match.group(1).strip() if match else item.strip()
        value = match.group(2).replace(',', '') if match and match.group(2) else str(average_value)
        multiplier = 1
        if 'K' in value:  # 'K' multiplier present
            multiplier = 1000
        elif 'M' in value:  # 'M' multiplier present
            multiplier = 1000000
        value = float(value[:-1]) * multiplier  # Remove 'K' or 'M' and apply multiplier
        trending_dict[key] = int(value)

    return trending_dict


def get_normalized_WRDCLD():
    with sync_playwright() as p:
        context = p.firefox.launch_persistent_context(user_data_path_, headless=True)  # False
        page = context.new_page()
        page.goto('https://twitter.com')
        page.wait_for_load_state("load")

        page.wait_for_timeout(6000)

        page.goto("https://twitter.com/explore/tabs/trending")
        page.wait_for_timeout(3000)

        for _ in range(5):
            page_content = page.content()

            soup = BeautifulSoup(page_content, 'html.parser')

            trending_tags = soup.select('div.css-175oi2r[aria-label="Timeline: Explore"] div['
                                        'data-testid="cellInnerDiv"]')

            for tag in trending_tags:
                text = tag.get_text(strip=True)
                trending_set.add(text)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        print("Raw Data trending : ", trending_set)

        for item in trending_set:
            splt_item = item.split('·Trending')
            if len(splt_item) == 2:
                final.append(splt_item[1])
            splt_item = item.split('·Politics · Trending')
            if len(splt_item) == 2:
                final.append(splt_item[1])
            splt_item = item.split('·Only on X · Trending')
            if len(splt_item) == 2:
                final.append(splt_item[1])

        print("Split trending : ", final)

        result_dict = process_trending_data(final)

        print("Postprocess trending : ", result_dict)

        page.wait_for_timeout(3000)
        page.goto("https://twitter.com/explore/tabs/news_unified")
        trending_set.clear()

        for _ in range(5):
            page_content = page.content()

            soup = BeautifulSoup(page_content, 'html.parser')

            trending_tags = soup.select('div.css-175oi2r[aria-label="Timeline: Explore"] div['
                                        'data-testid="cellInnerDiv"]')

            for tag in trending_tags:
                text = tag.get_text(strip=True)
                trending_set.add(text)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        print("Raw news : ", trending_set)

        for item in trending_set:
            splt_item = item.split('Trending in Politics')
            if len(splt_item) == 2:
                final2.append(splt_item[1])
            splt_item = item.split('Politics · Trending')
            if len(splt_item) == 2:
                final2.append(splt_item[1])

        print("Split news : ", final2)

        temp_store = process_trending_data(final2)

        print("Postprocess news : ", temp_store)

        result_dict.update(temp_store)

        print(result_dict)

        values = np.array(list(result_dict.values()))
        print(values)
        scaled_values = np.log(values + 1)
        normalized_values = (scaled_values - scaled_values.min()) / (scaled_values.max() - scaled_values.min())
        normalized_dict = dict(zip(result_dict.keys(), normalized_values))

    return normalized_dict


def store_data_in_mysql(data_dict):
    connection = connector.connect(
        host='datastuntstaging.co.in',
        user='u385679644_youtube_trans',
        password='~hHElD~U>n?2',
        database='u385679644_youtube_trans'
    )

    cursor = connection.cursor()

    try:
        connection.start_transaction()

        cursor.execute('TRUNCATE TABLE  trendingtweetreplica')

        for key, value in data_dict.items():
            cursor.execute('''
                INSERT INTO  trendingtweetreplica (key, value) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE value = VALUES(value)
            ''', (key, value))

        connection.commit()

    except connector.Error as err:
        print(f"Error: {err}")
        connection.rollback()

    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()


@app.route('/fetch_and_store_trending_data', methods=['GET'])
def fetch_and_store_trending_data():
    try:
        result_trend = get_normalized_WRDCLD()
        store_data_in_mysql(result_trend)
        return jsonify({"status": "success", "message": "WordCloud data fetched and stored successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(port=5000)

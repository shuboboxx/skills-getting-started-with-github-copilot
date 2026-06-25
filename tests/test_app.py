"""
Mergington 高中活動管理系統 API 測試

此文件使用 AAA（安排-執行-驗證）模式來組織測試，
使每個測試的結構更清晰易懂。
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """建立測試用戶端"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """重設活動資料到初始狀態"""
    # 保存原始資料
    original_participants = {
        key: val.get("participants", []).copy()
        for key, val in activities.items()
    }
    
    yield
    
    # 恢復原始資料
    for key in activities:
        activities[key]["participants"] = original_participants[key].copy()


class TestGetActivities:
    """測試獲取活動列表功能"""
    
    def test_get_all_activities(self, client, reset_activities):
        """
        驗證能否成功獲取所有活動
        
        安排: 使用測試用戶端
        執行: 發送 GET 請求到 /activities 端點
        驗證: 確認狀態碼為 200 且返回活動字典
        """
        # 安排
        expected_activities = ["Chess Club", "Programming Class", "Soccer Squad"]
        
        # 執行
        response = client.get("/activities")
        
        # 驗證
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """
        驗證每個活動都包含必要欄位
        
        安排: 定義必要的活動欄位清單
        執行: 獲取所有活動並檢查每個欄位
        驗證: 確認所有活動都包含必要欄位
        """
        # 安排
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # 執行
        response = client.get("/activities")
        activities_data = response.json()
        
        # 驗證
        for activity_name, details in activities_data.items():
            assert required_fields.issubset(details.keys()), \
                f"活動 {activity_name} 缺少必要欄位"
    
    def test_participants_are_list_of_strings(self, client, reset_activities):
        """
        驗證參與者欄位為字串清單
        
        安排: 獲取活動資料
        執行: 檢查每個活動的參與者清單
        驗證: 確認參與者都是字串格式
        """
        # 安排
        # （無需特殊安排）
        
        # 執行
        response = client.get("/activities")
        activities_data = response.json()
        
        # 驗證
        for activity_name, details in activities_data.items():
            assert isinstance(details["participants"], list), \
                f"活動 {activity_name} 的參與者不是清單"
            for participant in details["participants"]:
                assert isinstance(participant, str), \
                    f"參與者 {participant} 不是字串"


class TestStudentSignup:
    """測試學生報名功能"""
    
    def test_new_student_signup_success(self, client, reset_activities):
        """
        驗證新學生能否成功報名
        
        安排: 準備活動名稱和新學生電子郵件
        執行: 發送報名請求
        驗證: 確認返回成功消息
        """
        # 安排
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # 執行
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]
    
    def test_signup_to_nonexistent_activity_fails(self, client, reset_activities):
        """
        驗證報名不存在的活動時返回 404 錯誤
        
        安排: 定義不存在的活動名稱
        執行: 嘗試報名該活動
        驗證: 確認返回 404 狀態碼
        """
        # 安排
        nonexistent_activity = "Fake Club"
        email = "student@mergington.edu"
        
        # 執行
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_duplicate_signup_fails(self, client, reset_activities):
        """
        驗證重複報名返回錯誤
        
        安排: 選擇已有參與者的活動
        執行: 嘗試用同一電子郵件報名
        驗證: 確認返回 400 狀態碼和相關錯誤訊息
        """
        # 安排
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # 執行
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_email_normalization_prevents_duplicate(self, client, reset_activities):
        """
        驗證電子郵件大小寫正規化防止重複報名
        
        安排: 準備活動和大小寫不同的電子郵件
        執行: 先用混合大小寫報名，再用小寫報名
        驗證: 第二次報名應該失敗
        """
        # 安排
        activity_name = "Swimming Team"
        email_mixed_case = "NewStudent@MERGINGTON.EDU"
        email_lowercase = "newstudent@mergington.edu"
        
        # 執行 - 第一次報名
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email_mixed_case}",
            headers={"Content-Type": "application/json"}
        )
        assert response1.status_code == 200
        
        # 執行 - 第二次報名（不同大小寫）
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email_lowercase}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_increases_participant_count(self, client, reset_activities):
        """
        驗證成功報名後參與者數量增加
        
        安排: 記錄報名前的參與者數量
        執行: 報名新學生
        驗證: 確認參與者數量增加了 1
        """
        # 安排
        activity_name = "Drama Club"
        new_email = "newactor@mergington.edu"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        # 執行
        client.post(
            f"/activities/{activity_name}/signup?email={new_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        assert count_after == count_before + 1


class TestRemoveParticipant:
    """測試移除參與者功能"""
    
    def test_remove_existing_participant_success(self, client, reset_activities):
        """
        驗證能否成功移除現有參與者
        
        安排: 選擇現有參與者
        執行: 發送刪除請求
        驗證: 確認返回成功消息
        """
        # 安排
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        
        # 執行
        response = client.delete(
            f"/activities/{activity_name}/remove?email={email_to_remove}"
        )
        
        # 驗證
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Removed" in data["message"]
    
    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """
        驗證從不存在的活動移除參與者時返回 404
        
        安排: 定義不存在的活動名稱
        執行: 嘗試從該活動移除參與者
        驗證: 確認返回 404 狀態碼
        """
        # 安排
        nonexistent_activity = "Fake Club"
        email = "student@mergington.edu"
        
        # 執行
        response = client.delete(
            f"/activities/{nonexistent_activity}/remove?email={email}"
        )
        
        # 驗證
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """
        驗證移除不存在的參與者時返回 400 錯誤
        
        安排: 定義不存在的電子郵件
        執行: 嘗試移除不存在的參與者
        驗證: 確認返回 400 狀態碼
        """
        # 安排
        activity_name = "Chess Club"
        nonexistent_email = "nonexistent@mergington.edu"
        
        # 執行
        response = client.delete(
            f"/activities/{activity_name}/remove?email={nonexistent_email}"
        )
        
        # 驗證
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_remove_updates_participant_list(self, client, reset_activities):
        """
        驗證移除參與者後清單被更新
        
        安排: 記錄移除前的參與者資訊
        執行: 移除指定參與者
        驗證: 確認參與者從清單中移除
        """
        # 安排
        activity_name = "Soccer Squad"
        email_to_remove = "lisa@mergington.edu"
        
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity_name]["participants"]
        assert email_to_remove in participants_before
        
        # 執行
        client.delete(
            f"/activities/{activity_name}/remove?email={email_to_remove}"
        )
        
        # 驗證
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        assert email_to_remove not in participants_after
        assert len(participants_after) == len(participants_before) - 1
    
    def test_removed_participant_can_signup_again(self, client, reset_activities):
        """
        驗證移除參與者後可以重新報名
        
        安排: 記錄要移除的參與者
        執行: 先移除參與者，再嘗試重新報名
        驗證: 確認重新報名成功
        """
        # 安排
        activity_name = "Art Workshop"
        email = "maya@mergington.edu"
        
        # 執行 - 移除
        client.delete(
            f"/activities/{activity_name}/remove?email={email}"
        )
        
        # 執行 - 重新報名
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response.status_code == 200


class TestActivityCapacity:
    """測試活動容量限制"""
    
    def test_cannot_signup_when_activity_full(self, client, reset_activities):
        """
        驗證當活動已滿時無法報名
        
        安排: 建立容量為 1 且已滿的測試活動
        執行: 嘗試再報名一位學生
        驗證: 確認返回 400 狀態碼和容量已滿的錯誤訊息
        """
        # 安排
        test_activity = "Test Full Activity"
        activities[test_activity] = {
            "description": "已滿的測試活動",
            "schedule": "Monday",
            "max_participants": 1,
            "participants": ["full@mergington.edu"]
        }
        new_email = "another@mergington.edu"
        
        # 執行
        response = client.post(
            f"/activities/{test_activity}/signup?email={new_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()
        
        # 清理
        del activities[test_activity]
    
    def test_can_signup_when_spots_available(self, client, reset_activities):
        """
        驗證當活動有空位時能成功報名
        
        安排: 建立有多個空位的測試活動
        執行: 報名新學生
        驗證: 確認報名成功
        """
        # 安排
        test_activity = "Test Available Activity"
        activities[test_activity] = {
            "description": "有空位的測試活動",
            "schedule": "Tuesday",
            "max_participants": 5,
            "participants": ["one@mergington.edu", "two@mergington.edu"]
        }
        new_email = "three@mergington.edu"
        
        # 執行
        response = client.post(
            f"/activities/{test_activity}/signup?email={new_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # 驗證
        assert response.status_code == 200
        
        # 清理
        del activities[test_activity]

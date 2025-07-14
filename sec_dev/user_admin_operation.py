#!/usr/bin/env python3
# filepath: /home/renjie/ragflow/user_admin.py

"""
RAGFlow用户管理Admin类
结合API注册和数据库操作的完整用户管理工具
"""

import sys
import os
import requests
import json
import uuid
import base64
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# 添加RAGFlow项目路径到Python路径
sys.path.insert(0, '/home/renjie/ragflow')

from api.db.services.user_service import UserService, TenantService, UserTenantService
from api.db.db_models import init_database_tables, User, Tenant, UserTenant, DB, TenantLLM
from api import settings

class UserAdmin:
    """RAGFlow用户管理Admin类"""
    
    def __init__(self, ragflow_host="http://localhost:9380"):
        """
        初始化用户管理器
        
        Args:
            ragflow_host: RAGFlow服务器地址
        """
        self.host = ragflow_host.rstrip('/')
        self.session = requests.Session()
        self.db_initialized = False
        
        # 从文件加载RSA公钥
        self.public_key = self._load_public_key()
        
        # 初始化数据库
        self._init_database()
    
    def _load_public_key(self):
        """从conf/public.pem文件加载RSA公钥"""
        try:
            # 获取当前脚本所在目录的父目录，然后定位到conf/public.pem
            current_dir = os.path.dirname(os.path.abspath(__file__))
            ragflow_root = os.path.dirname(current_dir)  # 从sec_dev回到ragflow根目录
            public_key_path = os.path.join(ragflow_root, 'conf', 'public.pem')
            
            with open(public_key_path, 'r', encoding='utf-8') as f:
                public_key_content = f.read().strip()
            
            print(f"✅ 成功从 {public_key_path} 加载公钥")
            return public_key_content
            
        except FileNotFoundError:
            print(f"❌ 公钥文件不存在: {public_key_path}")
            raise FileNotFoundError(f"公钥文件不存在: {public_key_path}")
        except Exception as e:
            print(f"❌ 读取公钥文件失败: {e}")
            raise Exception(f"读取公钥文件失败: {e}")

    def _init_database(self):
        """初始化数据库连接"""
        try:
            settings.init_settings()
            init_database_tables()
            self.db_initialized = True
            print("✅ 数据库连接初始化成功")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            self.db_initialized = False
    
    def encrypt_password(self, password):
        """
        使用RSA公钥加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 加密后的密码（Base64编码）
        """
        try:
            password_b64 = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            rsa_key = RSA.importKey(self.public_key)
            cipher = PKCS1_v1_5.new(rsa_key)
            encrypted_password = cipher.encrypt(password_b64.encode('utf-8'))
            return base64.b64encode(encrypted_password).decode('utf-8')
        except Exception as e:
            print(f"❌ 密码加密失败: {e}")
            return None
    
    def check_server_status(self):
        """检查RAGFlow服务器状态"""
        try:
            health_url = f"{self.host}/v1/user/login/channels"
            response = self.session.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ RAGFlow服务器运行正常 ({self.host})")
                return True
            else:
                print(f"⚠️ RAGFlow服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ RAGFlow服务器无法访问: {e}")
            return False
    
    def register_user_and_get_api_token(self, nickname, email, password):
        """
        注册用户并获取API token
        
        Args:
            nickname: 用户昵称
            email: 用户邮箱
            password: 用户密码（明文）
            
        Returns:
            dict: 包含用户信息和api_token的完整信息
        """
        if not self.check_server_status():
            print("❌ RAGFlow服务器不可用，无法注册用户")
            return None
        
        # 1. 注册用户
        register_result = self._register_user(nickname, email, password)
        if not register_result:
            return None
        
        user_info = register_result.get('data', {})
        print(f"✅ 用户注册成功: {nickname} (ID: {user_info.get('id')})")
        
        # 2. 获取API token
        api_token = self._get_api_token()
        if not api_token:
            print("⚠️ 用户注册成功，但获取API token失败")
            return {
                "user": user_info,
                "api_token": None,
                "message": "用户注册成功，但API token获取失败"
            }
        
        # 3. 返回完整信息
        complete_info = {
            "user": {
                "id": user_info.get('id'),
                "nickname": user_info.get('nickname'),
                "email": user_info.get('email'),
                "create_time": user_info.get('create_time'),
                "access_token": user_info.get('access_token')
            },
            "api_token": api_token,
            "tenant_id": user_info.get('id'),  # 通常用户ID就是tenant_id
            "success": True
        }
        
        print(f"✅ API Token获取成功: {api_token}")
        return complete_info
    
    def _register_user(self, nickname, email, password):
        """内部方法：注册用户"""
        register_url = f"{self.host}/v1/user/register"
        
        # 加密密码
        encrypted_password = self.encrypt_password(password)
        if not encrypted_password:
            return None
        
        payload = {
            "nickname": nickname,
            "email": email,
            "password": encrypted_password
        }
        
        try:
            print(f"🔗 通过API注册用户: {nickname} ({email})")
            response = self.session.post(register_url, json=payload)
            result = response.json()
            
            if result.get('code') == 0:
                # 设置认证头用于后续API调用
                auth_token = response.headers.get('Authorization')
                if auth_token:
                    self.session.headers.update({'Authorization': auth_token})
                return result
            else:
                error_msg = result.get('message', '未知错误')
                print(f"❌ 用户注册失败: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ API注册请求失败: {e}")
            return None
    
    def _get_api_token(self):
        """内部方法：获取API token"""
        token_url = f"{self.host}/v1/system/new_token"
        
        try:
            response = self.session.post(token_url, json={})
            result = response.json()
            
            if result.get('code') == 0:
                token_data = result.get('data', {})
                api_token = token_data.get('token')
                return api_token
            else:
                print(f"❌ API Token创建失败: {result.get('message', '未知错误')}")
                return None
        except Exception as e:
            print(f"❌ Token创建请求失败: {e}")
            return None
    
    def list_users(self):
        """列出所有用户（通过数据库）"""
        if not self.db_initialized:
            print("❌ 数据库未初始化")
            return []
        
        try:
            with DB.connection_context():
                users = User.select()
            
            if not users:
                print("📭 没有找到用户")
                return []
            
            user_list = []
            print("\n📋 用户列表:")
            print("-" * 110)
            print(f"{'ID':<32} {'昵称':<15} {'邮箱':<30} {'状态':<5} {'超级用户':<8} {'登录渠道':<10}")
            print("-" * 110)
            
            for user in users:
                status_text = "有效" if user.status == "1" else "无效"
                superuser_text = "是" if user.is_superuser else "否"
                print(f"{user.id:<32} {user.nickname:<15} {user.email:<30} {status_text:<5} {superuser_text:<8} {user.login_channel:<10}")
                user_list.append({
                    'id': user.id,
                    'nickname': user.nickname,
                    'email': user.email,
                    'status': user.status,
                    'is_superuser': user.is_superuser,
                    'login_channel': user.login_channel
                })
            
            print("-" * 110)
            print(f"总计: {len(user_list)} 个用户")
            return user_list
            
        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")
            return []
    
    def get_user_details(self, user_id):
        """获取用户详细信息（通过数据库）"""
        if not self.db_initialized:
            print("❌ 数据库未初始化")
            return None
        
        try:
            with DB.connection_context():
                user = User.select().where(User.id == user_id).first()
                if not user:
                    print(f"❌ 用户 {user_id} 不存在")
                    return None
                
                # 获取租户信息
                tenant = Tenant.select().where(Tenant.id == user_id).first()
                user_tenant = UserTenant.select().where(UserTenant.user_id == user_id).first()
                tenant_llm_count = TenantLLM.select().where(TenantLLM.tenant_id == user_id).count()
                
            print(f"\n📄 用户详细信息:")
            print(f"   👤 用户ID: {user.id}")
            print(f"   👤 昵称: {user.nickname}")
            print(f"   📧 邮箱: {user.email}")
            print(f"   🔒 状态: {'有效' if user.status == '1' else '无效'}")
            print(f"   👑 超级用户: {'是' if user.is_superuser else '否'}")
            print(f"   🚪 登录渠道: {user.login_channel}")
            print(f"   🕐 最后登录: {user.last_login_time}")
            print(f"   📅 创建时间: {user.create_time}")
            print(f"   📅 更新时间: {user.update_time}")
            
            if tenant:
                print(f"\n🏢 租户信息:")
                print(f"   🏢 租户ID: {tenant.id}")
                print(f"   🏢 租户名称: {tenant.name}")
                print(f"   🤖 LLM模型: {tenant.llm_id}")
                print(f"   🔤 嵌入模型: {tenant.embd_id}")
            
            if user_tenant:
                print(f"\n🔗 用户-租户关联:")
                print(f"   🔗 关联ID: {user_tenant.id}")
                print(f"   👑 角色: {user_tenant.role}")
                print(f"   👥 邀请者: {user_tenant.invited_by}")
            
            print(f"\n⚙️  LLM配置数量: {tenant_llm_count}")
            
            return user
            
        except Exception as e:
            print(f"❌ 获取用户详情失败: {e}")
            return None
    
    def delete_user(self, user_id, confirm=True):
        """
        完全删除用户（通过数据库）
        
        Args:
            user_id: 用户ID
            confirm: 是否需要确认（默认True）
        """
        if not self.db_initialized:
            print("❌ 数据库未初始化")
            return False
        
        try:
            # 先获取用户信息
            user_details = self.get_user_details(user_id)
            if not user_details:
                return False
            
            if confirm:
                print(f"\n⚠️  警告：这将完全删除用户及其所有相关数据！")
                print(f"   包括：用户记录、租户、用户-租户关联、LLM配置等")
                
                confirm_input = input(f"\n确认要完全删除用户 {user_details.nickname} ({user_details.email}) 吗? (输入 'DELETE' 确认): ").strip()
                if confirm_input != 'DELETE':
                    print("❌ 操作已取消")
                    return False
            
            print(f"🗑️  正在完全删除用户...")
            
            # 使用rollback_user_registration函数的逻辑
            self._rollback_user_registration(user_id)
            
            # 验证删除结果
            with DB.connection_context():
                user_exists = User.select().where(User.id == user_id).exists()
                tenant_exists = Tenant.select().where(Tenant.id == user_id).exists()
            
            if not user_exists and not tenant_exists:
                print(f"✅ 用户 {user_details.nickname} ({user_details.email}) 及相关数据已完全删除")
                return True
            else:
                print(f"❌ 删除可能不完整，请检查")
                return False
                
        except Exception as e:
            print(f"❌ 删除用户失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _rollback_user_registration(self, user_id):
        """
        删除用户注册时创建的所有相关数据
        复制自api.apps.user_app.rollback_user_registration
        """
        try:
            UserService.delete_by_id(user_id)
        except Exception:
            pass
        try:
            TenantService.delete_by_id(user_id)
        except Exception:
            pass
        try:
            u = UserTenantService.query(tenant_id=user_id)
            if u:
                UserTenantService.delete_by_id(u[0].id)
        except Exception:
            pass
        try:
            TenantLLM.delete().where(TenantLLM.tenant_id == user_id).execute()
        except Exception:
            pass
    
    def create_test_user(self, user_suffix=None):
        """
        创建测试用户的便捷方法
        
        Args:
            user_suffix: 用户后缀，如果不提供则自动生成
        
        Returns:
            dict: 包含用户信息和api_token
        """
        if not user_suffix:
            user_suffix = str(uuid.uuid4())[:8]
        
        nickname = f"TestUser_{user_suffix}"
        email = f"user_{user_suffix}@example.com"
        password = "Test123456"
        
        print(f"🎯 创建测试用户:")
        print(f"   昵称: {nickname}")
        print(f"   邮箱: {email}")
        print(f"   密码: {password}")
        print("-" * 50)
        
        result = self.register_user_and_get_api_token(nickname, email, password)
        
        if result and result.get('success'):
            print("\n📋 用户创建成功:")
            print(f"   用户ID: {result['user']['id']}")
            print(f"   昵称: {result['user']['nickname']}")
            print(f"   邮箱: {result['user']['email']}")
            print(f"   API Token: {result['api_token']}")
            print(f"   Tenant ID: {result['tenant_id']}")
            
            # 保存到文件
            filename = f"ragflow_user_{user_suffix}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   💾 用户信息已保存到: {filename}")
        
        return result
    
    def admin_menu(self):
        """管理员菜单"""
        print("🚀 RAGFlow UserAdmin 管理工具")
        print("=" * 60)
        
        if not self.db_initialized:
            print("❌ 数据库未初始化，请检查配置")
            return
        
        while True:
            print("\n📋 管理员操作菜单:")
            print("1. 列出所有用户")
            print("2. 查看用户详情")
            print("3. 注册新用户并获取API Token")
            print("4. 创建测试用户")
            print("5. 删除用户")
            print("6. 检查服务器状态")
            print("0. 退出")
            
            choice = input("\n请选择操作 (0-6): ").strip()
            
            if choice == "0":
                print("👋 再见!")
                break
            elif choice == "1":
                self.list_users()
            elif choice == "2":
                user_id = input("请输入用户ID: ").strip()
                if user_id:
                    self.get_user_details(user_id)
            elif choice == "3":
                nickname = input("请输入用户昵称: ").strip()
                email = input("请输入用户邮箱: ").strip()
                password = input("请输入用户密码: ").strip()
                if nickname and email and password:
                    result = self.register_user_and_get_api_token(nickname, email, password)
                    if result and result.get('api_token'):
                        print(f"\n🔑 API Token: {result['api_token']}")
            elif choice == "4":
                user_suffix = input("请输入用户后缀（留空自动生成）: ").strip()
                self.create_test_user(user_suffix if user_suffix else None)
            elif choice == "5":
                user_id = input("请输入要删除的用户ID: ").strip()
                if user_id:
                    self.delete_user(user_id)
            elif choice == "6":
                self.check_server_status()
            else:
                print("❌ 无效的选择")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAGFlow UserAdmin 管理工具')
    parser.add_argument('--host', default='http://localhost:9380', help='RAGFlow服务器地址')
    parser.add_argument('command', nargs='?', choices=['list', 'info', 'delete', 'create', 'test'], help='操作命令')
    parser.add_argument('target', nargs='?', help='操作目标（用户ID等）')
    parser.add_argument('--nickname', help='用户昵称')
    parser.add_argument('--email', help='用户邮箱')
    parser.add_argument('--password', help='用户密码')
    
    args = parser.parse_args()
    
    # 创建管理器实例
    user_admin = UserAdmin(args.host)
    
    if args.command:
        # 命令行模式
        if args.command == 'list':
            user_admin.list_users()
        elif args.command == 'info' and args.target:
            user_admin.get_user_details(args.target)
        elif args.command == 'delete' and args.target:
            user_admin.delete_user(args.target)
        elif args.command == 'create' and args.nickname and args.email and args.password:
            result = user_admin.register_user_and_get_api_token(args.nickname, args.email, args.password)
            if result and result.get('api_token'):
                print(f"\n🔑 API Token: {result['api_token']}")
        elif args.command == 'test':
            user_admin.create_test_user(args.target)
        else:
            print("❌ 参数不完整")
    else:
        # 交互模式
        user_admin.admin_menu()


if __name__ == "__main__":
    main()
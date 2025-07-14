"""
基于官方 RAGFlow SDK 的客户端实现
使用 pip install ragflow-sdk 安装官方 SDK
"""

import json
import os
import sys
from typing import Optional, Dict, Any, List, Union
import logging

from ragflow_sdk import RAGFlow, DataSet, Chat, Session, Document, Chunk, Agent

class RAGFlowSDKClient:
    """RAGFlow SDK 官方客户端封装"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:9380",
                 api_token: str = None):
        """
        初始化RAGFlow SDK客户端
        
        Args:
            base_url: RAGFlow服务器地址
            api_token: API认证token（必需）
        """
        if not api_token:
            raise ValueError("api_token 是必需的参数")
            
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        
        # 初始化 RAGFlow SDK
        self.rag = RAGFlow(api_key=api_token, base_url=base_url)
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    # ============ 数据集管理 ============
    
    def create_dataset(self, 
                      name: str,
                      description: str = "",
                      embedding_model: str = "BAAI/bge-large-zh-v1.5@BAAI",
                      permission: str = "me",
                      chunk_method: str = "naive") -> DataSet:
        """创建数据集"""
        try:
            dataset = self.rag.create_dataset(
                name=name,
                description=description,
                embedding_model=embedding_model,
                permission=permission,
                chunk_method=chunk_method
            )
            self.logger.info(f"成功创建数据集: {name}")
            return dataset
        except Exception as e:
            self.logger.error(f"创建数据集失败: {e}")
            raise
    
    def list_datasets(self, 
                     page: int = 1,
                     page_size: int = 30,
                     name: str = None) -> List[DataSet]:
        """列出数据集"""
        try:
            datasets = self.rag.list_datasets(
                page=page,
                page_size=page_size,
                name=name
            )
            self.logger.info(f"获取到 {len(datasets)} 个数据集")
            return datasets
        except Exception as e:
            self.logger.error(f"获取数据集列表失败: {e}")
            raise
    
    def delete_datasets(self, dataset_ids: List[str] = None):
        """删除数据集"""
        try:
            self.rag.delete_datasets(ids=dataset_ids)
            self.logger.info(f"成功删除数据集: {dataset_ids}")
        except Exception as e:
            self.logger.error(f"删除数据集失败: {e}")
            raise
    
    def get_dataset_by_name(self, name: str) -> DataSet:
        """根据名称获取数据集"""
        try:
            return self.rag.get_dataset(name=name)
        except Exception as e:
            self.logger.error(f"获取数据集失败: {e}")
            raise
    
    # ============ 文档管理 ============
    
    def upload_document_to_dataset(self, 
                                  dataset: DataSet,
                                  file_path: str,
                                  display_name: str = None) -> None:
        """上传文档到数据集"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                blob = f.read()
            
            if not display_name:
                display_name = os.path.basename(file_path)
            
            documents = [{"display_name": display_name, "blob": blob}]
            dataset.upload_documents(documents)
            self.logger.info(f"成功上传文档: {display_name}")
        except Exception as e:
            self.logger.error(f"上传文档失败: {e}")
            raise
    
    def list_documents(self, 
                      dataset: DataSet,
                      keywords: str = None,
                      page: int = 1,
                      page_size: int = 30) -> List[Document]:
        """列出数据集中的文档"""
        try:
            documents = dataset.list_documents(
                keywords=keywords,
                page=page,
                page_size=page_size
            )
            self.logger.info(f"获取到 {len(documents)} 个文档")
            return documents
        except Exception as e:
            self.logger.error(f"获取文档列表失败: {e}")
            raise
    
    def delete_documents(self, dataset: DataSet, document_ids: List[str] = None):
        """删除文档"""
        try:
            dataset.delete_documents(ids=document_ids)
            self.logger.info(f"成功删除文档: {document_ids}")
        except Exception as e:
            self.logger.error(f"删除文档失败: {e}")
            raise
    
    def parse_documents(self, dataset: DataSet, document_ids: List[str]):
        """解析文档"""
        try:
            dataset.async_parse_documents(document_ids)
            self.logger.info(f"开始解析文档: {document_ids}")
        except Exception as e:
            self.logger.error(f"解析文档失败: {e}")
            raise
    
    def stop_parsing_documents(self, dataset: DataSet, document_ids: List[str]):
        """停止解析文档"""
        try:
            dataset.async_cancel_parse_documents(document_ids)
            self.logger.info(f"停止解析文档: {document_ids}")
        except Exception as e:
            self.logger.error(f"停止解析文档失败: {e}")
            raise
    
    # ============ 块管理 ============
    
    def add_chunk_to_document(self, 
                             document: Document,
                             content: str,
                             important_keywords: List[str] = []) -> Chunk:
        """添加块到文档"""
        try:
            chunk = document.add_chunk(
                content=content,
                important_keywords=important_keywords
            )
            self.logger.info(f"成功添加块到文档: {document.id}")
            return chunk
        except Exception as e:
            self.logger.error(f"添加块失败: {e}")
            raise
    
    def list_chunks(self, 
                   document: Document,
                   keywords: str = None,
                   page: int = 1,
                   page_size: int = 30) -> List[Chunk]:
        """列出文档中的块"""
        try:
            chunks = document.list_chunks(
                keywords=keywords,
                page=page,
                page_size=page_size
            )
            self.logger.info(f"获取到 {len(chunks)} 个块")
            return chunks
        except Exception as e:
            self.logger.error(f"获取块列表失败: {e}")
            raise
    
    def delete_chunks(self, document: Document, chunk_ids: List[str] = None):
        """删除块"""
        try:
            document.delete_chunks(chunk_ids)
            self.logger.info(f"成功删除块: {chunk_ids}")
        except Exception as e:
            self.logger.error(f"删除块失败: {e}")
            raise
    
    def retrieve_chunks(self,
                       question: str,
                       dataset_ids: List[str],
                       document_ids: List[str] = None,
                       page: int = 1,
                       page_size: int = 30,
                       similarity_threshold: float = 0.2,
                       vector_similarity_weight: float = 0.3,
                       top_k: int = 1024) -> List[Chunk]:
        """检索块"""
        try:
            chunks = self.rag.retrieve(
                question=question,
                dataset_ids=dataset_ids,
                document_ids=document_ids,
                page=page,
                page_size=page_size,
                similarity_threshold=similarity_threshold,
                vector_similarity_weight=vector_similarity_weight,
                top_k=top_k
            )
            self.logger.info(f"检索到 {len(chunks)} 个相关块")
            return chunks
        except Exception as e:
            self.logger.error(f"检索块失败: {e}")
            raise
    
    # ============ 聊天助手管理 ============
    
    def create_chat_assistant(self,
                             name: str,
                             dataset_ids: List[str] = [],
                             avatar: str = "",
                             llm_config: Dict = None,
                             prompt_config: Dict = None) -> Chat:
        """创建聊天助手"""
        try:
            # 设置默认的LLM配置
            if llm_config is None:
                llm_config = {
                    "model_name": "qwen3:32b",
                    "temperature": 0.1,
                    "top_p": 0.3,
                }
            
            # 创建LLM对象
            llm = Chat.LLM(self.rag, llm_config)
            
            # 设置默认的Prompt配置  
            if prompt_config is None:
                prompt_config = {
                    "similarity_threshold": 0.2,
                    "keywords_similarity_weight": 0.7,
                    "top_n": 8,
                    "opener": "你好！我是你的AI助手，有什么可以帮助你的吗？"
                }
            
            # 创建Prompt对象
            prompt = Chat.Prompt(self.rag, prompt_config)
            
            chat = self.rag.create_chat(
                name=name,
                avatar=avatar,
                dataset_ids=dataset_ids,
                llm=llm,
                prompt=prompt
            )
            self.logger.info(f"成功创建聊天助手: {name}")
            return chat
        except Exception as e:
            self.logger.error(f"创建聊天助手失败: {e}")
            raise
    
    def list_chat_assistants(self,
                           page: int = 1,
                           page_size: int = 30,
                           name: str = None) -> List[Chat]:
        """列出聊天助手"""
        try:
            chats = self.rag.list_chats(
                page=page,
                page_size=page_size,
                name=name
            )
            self.logger.info(f"获取到 {len(chats)} 个聊天助手")
            return chats
        except Exception as e:
            self.logger.error(f"获取聊天助手列表失败: {e}")
            raise
    
    def delete_chat_assistants(self, chat_ids: List[str] = None):
        """删除聊天助手"""
        try:
            self.rag.delete_chats(ids=chat_ids)
            self.logger.info(f"成功删除聊天助手: {chat_ids}")
        except Exception as e:
            self.logger.error(f"删除聊天助手失败: {e}")
            raise
    
    # ============ 会话管理 ============
    
    def create_session(self, chat: Chat, name: str = "新会话") -> Session:
        """创建会话"""
        try:
            session = chat.create_session(name=name)
            self.logger.info(f"成功创建会话: {name}")
            return session
        except Exception as e:
            self.logger.error(f"创建会话失败: {e}")
            raise
    
    def list_sessions(self,
                     chat: Chat,
                     page: int = 1,
                     page_size: int = 30,
                     name: str = None) -> List[Session]:
        """列出会话"""
        try:
            sessions = chat.list_sessions(
                page=page,
                page_size=page_size,
                name=name
            )
            self.logger.info(f"获取到 {len(sessions)} 个会话")
            return sessions
        except Exception as e:
            self.logger.error(f"获取会话列表失败: {e}")
            raise
    
    def delete_sessions(self, chat: Chat, session_ids: List[str] = None):
        """删除会话"""
        try:
            chat.delete_sessions(ids=session_ids)
            self.logger.info(f"成功删除会话: {session_ids}")
        except Exception as e:
            self.logger.error(f"删除会话失败: {e}")
            raise
    
    def chat_with_assistant(self,
                           session: Session,
                           question: str,
                           stream: bool = False):
        """与聊天助手对话"""
        try:
            if stream:
                # 流式响应
                self.logger.info("开始流式对话")
                return session.ask(question=question, stream=True)
            else:
                # 非流式响应
                response = session.ask(question=question, stream=False)
                self.logger.info("获得对话响应")
                return response
        except Exception as e:
            self.logger.error(f"对话失败: {e}")
            raise
    
    # ============ Agent管理 ============
    
    def list_agents(self,
                   page: int = 1,
                   page_size: int = 30,
                   title: str = None) -> List[Agent]:
        """列出Agent"""
        try:
            agents = self.rag.list_agents(
                page=page,
                page_size=page_size,
                title=title
            )
            self.logger.info(f"获取到 {len(agents)} 个Agent")
            return agents
        except Exception as e:
            self.logger.error(f"获取Agent列表失败: {e}")
            raise
    
    def create_agent(self,
                    title: str,
                    dsl: Dict,
                    description: str = None) -> None:
        """创建Agent"""
        try:
            self.rag.create_agent(
                title=title,
                dsl=dsl,
                description=description
            )
            self.logger.info(f"成功创建Agent: {title}")
        except Exception as e:
            self.logger.error(f"创建Agent失败: {e}")
            raise
    
    def update_agent(self,
                    agent_id: str,
                    title: str = None,
                    description: str = None,
                    dsl: Dict = None) -> None:
        """更新Agent"""
        try:
            self.rag.update_agent(
                agent_id=agent_id,
                title=title,
                description=description,
                dsl=dsl
            )
            self.logger.info(f"成功更新Agent: {agent_id}")
        except Exception as e:
            self.logger.error(f"更新Agent失败: {e}")
            raise
    
    def delete_agent(self, agent_id: str) -> None:
        """删除Agent"""
        try:
            self.rag.delete_agent(agent_id=agent_id)
            self.logger.info(f"成功删除Agent: {agent_id}")
        except Exception as e:
            self.logger.error(f"删除Agent失败: {e}")
            raise
    
    # ============ Agent会话管理 ============
    
    def create_agent_session(self, agent: Agent, **kwargs) -> Session:
        """创建Agent会话"""
        try:
            session = agent.create_session(**kwargs)
            self.logger.info(f"成功创建Agent会话")
            return session
        except Exception as e:
            self.logger.error(f"创建Agent会话失败: {e}")
            raise
    
    def list_agent_sessions(self,
                          agent: Agent,
                          page: int = 1,
                          page_size: int = 30) -> List[Session]:
        """列出Agent会话"""
        try:
            sessions = agent.list_sessions(
                page=page,
                page_size=page_size
            )
            self.logger.info(f"获取到 {len(sessions)} 个Agent会话")
            return sessions
        except Exception as e:
            self.logger.error(f"获取Agent会话列表失败: {e}")
            raise
    
    def delete_agent_sessions(self, agent: Agent, session_ids: List[str] = None):
        """删除Agent会话"""
        try:
            agent.delete_sessions(ids=session_ids)
            self.logger.info(f"成功删除Agent会话: {session_ids}")
        except Exception as e:
            self.logger.error(f"删除Agent会话失败: {e}")
            raise
    
    def chat_with_agent(self,
                       session: Session,
                       question: str = "",
                       stream: bool = False):
        """与Agent对话"""
        try:
            if stream:
                # 流式响应
                self.logger.info("开始与Agent流式对话")
                return session.ask(question=question, stream=True)
            else:
                # 非流式响应
                response = session.ask(question=question, stream=False)
                self.logger.info("获得Agent对话响应")
                return response
        except Exception as e:
            self.logger.error(f"与Agent对话失败: {e}")
            raise


def main():
    """主函数 - 演示完整的使用流程"""
    
    # 初始化客户端
    client = RAGFlowSDKClient(
        base_url="http://localhost:9380",
        api_token="ragflow-ZhNTIxYTcwNWUyYzExZjA5MzBkNmU1Nm"  # 替换为你的API token
    )
    
    try:
        print("=== RAGFlow SDK 客户端测试 ===")
        
        # 1. 数据集管理演示
        print("\n1. 创建数据集")
        dataset = client.create_dataset(
            name="测试数据集",
            description="这是一个测试数据集",
            chunk_method="naive"
        )
        print(f"数据集ID: {dataset.id}")
        
        # 2. 列出数据集
        print("\n2. 列出数据集")
        datasets = client.list_datasets()
        for ds in datasets:
            print(f"- {ds.name} ({ds.id})")
        
        # 3. 上传文档（如果存在测试文件）
        test_file = "/tmp/test.txt"
        if os.path.exists(test_file):
            print("\n3. 上传文档")
            client.upload_document_to_dataset(
                dataset=dataset,
                file_path=test_file,
                display_name="测试文档.txt"
            )
        else:
            print("\n3. 跳过文档上传（测试文件不存在）")
        
        # 4. 列出文档
        print("\n4. 列出文档")
        documents = client.list_documents(dataset)
        for doc in documents:
            print(f"- {doc.name} ({doc.id})")
        
        # 5. 创建聊天助手
        print("\n5. 创建聊天助手")
        chat_assistant = client.create_chat_assistant(
            name="测试助手",
            dataset_ids=[dataset.id]
        )
        print(f"聊天助手ID: {chat_assistant.id}")
        
        # 6. 列出聊天助手
        print("\n6. 列出聊天助手")
        chats = client.list_chat_assistants()
        for chat in chats:
            print(f"- {chat.name} ({chat.id})")
        
        # 7. 创建会话
        print("\n7. 创建会话")
        session = client.create_session(chat_assistant, "测试会话")
        print(f"会话ID: {session.id}")
        
        # 8. 对话测试
        print("\n8. 对话测试")
        response = client.chat_with_assistant(
            session=session,
            question="你好，请介绍一下自己",
            stream=False
        )
        print(f"助手回复: {response.content}")
        
        # 9. 流式对话测试
        print("\n9. 流式对话测试")
        print("助手回复（流式）: ", end="", flush=True)
        content = ""
        for chunk in client.chat_with_assistant(
            session=session,
            question="请简单介绍一下RAGFlow",
            stream=True
        ):
            new_content = chunk.content[len(content):]
            print(new_content, end="", flush=True)
            content = chunk.content
        print()
        
        # 10. 列出Agent
        print("\n10. 列出Agent")
        agents = client.list_agents()
        print(f"找到 {len(agents)} 个Agent")
        for agent in agents:
            print(f"- {agent.title if hasattr(agent, 'title') else 'Unknown'}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
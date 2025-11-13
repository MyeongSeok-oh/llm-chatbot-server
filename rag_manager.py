"""
rag_manager.py - RAG (Retrieval-Augmented Generation) 관리
RAG + Memory 통합 버전 (오류 수정)
"""
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from typing import List
from datetime import datetime
import os

from config import Config
from prompts import PromptManager


class RAGManager:
    """RAG 관리 클래스 - 메모리 통합"""

    def __init__(self, config: Config = None, prompt_manager: PromptManager = None, llm = None):
        """
        Args:
            config: 설정 객체
            prompt_manager: 프롬프트 관리자
            llm: LLM 모델 (LLMManager.llm)
        """
        self.config = config or Config()
        self.prompt_manager = prompt_manager or PromptManager()
        self.llm = llm

        print(f"[RAGManager] 임베딩 모델 로딩: {self.config.EMBEDDING_MODEL}")

        self.embeddings = self._initialize_embeddings()
        self.vectorstore = self._initialize_vectorstore()

        print(f"[RAGManager] RAG 초기화 완료")

    def _initialize_embeddings(self) -> OpenAIEmbeddings:
        """임베딩 모델 초기화"""
        embeddings = OpenAIEmbeddings(
            model=self.config.EMBEDDING_MODEL,
            openai_api_key=self.config.OPENAI_API_KEY
        )
        print(f"[RAGManager] 임베딩 모델 로딩 완료")
        return embeddings

    def _initialize_vectorstore(self) -> Chroma:
        """벡터 스토어 초기화"""
        print(f"[RAGManager] ChromaDB 초기화")

        # 텔레메트리 비활성화 (네트워크 오류 방지)
        os.environ["ANONYMIZED_TELEMETRY"] = "False"

        try:
            vectorstore = Chroma(
                persist_directory=self.config.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name="elderly_knowledge"
            )
            doc_count = vectorstore._collection.count()
            print(f"[RAGManager] ChromaDB 로드 완료 (문서 수: {doc_count})")
        except Exception as e:
            print(f"[RAGManager] 새 ChromaDB 생성")
            vectorstore = Chroma(
                persist_directory=self.config.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name="elderly_knowledge"
            )

        return vectorstore

    def create_retriever(self):
        """Retriever 생성"""
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.config.RETRIEVER_K}
        )

    def create_rag_chain(self):
        """
        RAG 체인 생성 (메모리 없음)
        """
        if not self.llm:
            raise ValueError("LLM이 설정되지 않았습니다!")

        retriever = self.create_retriever()

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_manager.get_prompt()),
            ("system", "다음은 관련 정보입니다:\n{context}"),
            ("human", "{question}")
        ])

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

    def create_rag_chain_with_memory(self):
        """
        ⭐ RAG + 메모리 통합 체인 생성
        """
        if not self.llm:
            raise ValueError("LLM이 설정되지 않았습니다!")

        retriever = self.create_retriever()

        # ⭐ 대화 기록을 포함하는 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_manager.get_prompt()),
            ("system", "다음은 검색된 관련 정보입니다:\n{context}"),
            MessagesPlaceholder(variable_name="chat_history"),  # ← 대화 기록
            ("human", "{question}")
        ])

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # ⭐ 수정: RunnablePassthrough 대신 명시적 함수 사용
        def get_question(x):
            if isinstance(x, dict):
                return x.get("question", "")
            return x

        def get_history(x):
            if isinstance(x, dict):
                return x.get("chat_history", [])
            return []

        rag_chain = (
            {
                "context": lambda x: format_docs(retriever.invoke(get_question(x))),
                "question": get_question,
                "chat_history": get_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

    def generate_with_rag(self, query: str) -> tuple[str, List[Document]]:
        """
        RAG를 사용한 응답 생성 (메모리 없음)

        Args:
            query: 사용자 질문

        Returns:
            tuple: (응답, 출처 문서 리스트)
        """
        rag_chain = self.create_rag_chain()
        retriever = self.create_retriever()

        # 응답 생성
        response = rag_chain.invoke(query)

        # 출처 문서 검색
        source_docs = retriever.invoke(query)

        return response, source_docs

    def generate_with_rag_and_memory(
        self,
        query: str,
        chat_history: List
    ) -> tuple[str, List[Document]]:
        """
        ⭐ RAG + 메모리를 사용한 응답 생성

        Args:
            query: 사용자 질문
            chat_history: 대화 기록 (LangChain Message 형식)

        Returns:
            tuple: (응답, 출처 문서 리스트)
        """
        print(f"[RAGManager] RAG + 메모리 모드: {len(chat_history)}개 대화 기록 사용")

        rag_chain = self.create_rag_chain_with_memory()
        retriever = self.create_retriever()

        # 응답 생성 (대화 기록 포함)
        response = rag_chain.invoke({
            "question": query,
            "chat_history": chat_history
        })

        # 출처 문서 검색
        source_docs = retriever.invoke(query)

        return response, source_docs

    def add_document(self, content: str, metadata: dict = None) -> dict:
        """
        문서 추가

        Args:
            content: 문서 내용
            metadata: 메타데이터

        Returns:
            dict: 결과 정보
        """
        try:
            # tiktoken 없이 작동하도록 간단한 분할 사용
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.CHUNK_SIZE,
                chunk_overlap=self.config.CHUNK_OVERLAP,
                length_function=len,
                is_separator_regex=False,  # tiktoken 사용 안 함
                separators=["\n\n", "\n", ". ", " ", ""]
            )

            chunks = text_splitter.split_text(content)

            documents = [
                Document(
                    page_content=chunk,
                    metadata=metadata or {
                        "source": "manual",
                        "timestamp": str(datetime.now())
                    }
                )
                for chunk in chunks
            ]

            self.vectorstore.add_documents(documents)

            print(f"[RAGManager] 문서 추가 완료 ({len(chunks)}개 청크)")

            return {
                "success": True,
                "chunks_created": len(chunks)
            }

        except Exception as e:
            print(f"[RAGManager] 문서 추가 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def search_documents(self, query: str, k: int = None) -> List[Document]:
        """
        문서 검색

        Args:
            query: 검색 쿼리
            k: 검색할 문서 수

        Returns:
            List[Document]: 검색된 문서 리스트
        """
        k = k or self.config.RETRIEVER_K
        docs = self.vectorstore.similarity_search(query, k=k)
        return docs

    def get_document_count(self) -> int:
        """벡터 DB의 문서 수 조회"""
        return self.vectorstore._collection.count()

    def clear_documents(self) -> bool:
        """벡터 DB 초기화"""
        try:
            import shutil

            if os.path.exists(self.config.CHROMA_PERSIST_DIR):
                shutil.rmtree(self.config.CHROMA_PERSIST_DIR)

            self.vectorstore = self._initialize_vectorstore()

            print(f"[RAGManager] 벡터 DB 초기화 완료")
            return True

        except Exception as e:
            print(f"[RAGManager] 초기화 실패: {e}")
            return False

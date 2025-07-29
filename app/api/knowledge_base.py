"""
知识库API路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import tempfile
import os
from pathlib import Path

from src.knowledge_base.knowledge_base_manager import knowledge_base_manager

router = APIRouter()


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """上传并处理单个文件"""
    try:
        # 检查文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_path = Path(file.filename)
        if not knowledge_base_manager.doc_processor.is_supported_file(file_path):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_path.suffix}"
            )
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_path.suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理文件
            result = await knowledge_base_manager.add_file(tmp_file_path)
            result["original_filename"] = file.filename
            return result
            
        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")


@router.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    """批量上传并处理文件"""
    results = []
    
    for file in files:
        try:
            # 检查文件类型
            if not file.filename:
                results.append({
                    "filename": "unknown",
                    "success": False,
                    "message": "文件名不能为空"
                })
                continue
            
            file_path = Path(file.filename)
            if not knowledge_base_manager.doc_processor.is_supported_file(file_path):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": f"不支持的文件格式: {file_path.suffix}"
                })
                continue
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_path.suffix) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # 处理文件
                result = await knowledge_base_manager.add_file(tmp_file_path)
                result["original_filename"] = file.filename
                results.append(result)
                
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
                
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "message": f"处理失败: {str(e)}"
            })
    
    # 统计结果
    total_files = len(results)
    successful_files = sum(1 for r in results if r.get("success", False))
    
    return {
        "total_files": total_files,
        "successful_files": successful_files,
        "failed_files": total_files - successful_files,
        "success_rate": (successful_files / total_files * 100) if total_files > 0 else 0,
        "results": results
    }


@router.post("/add-directory")
async def add_directory(directory_path: str, recursive: bool = True):
    """添加本地目录到知识库"""
    try:
        if not os.path.exists(directory_path):
            raise HTTPException(status_code=404, detail="目录不存在")
        
        if not os.path.isdir(directory_path):
            raise HTTPException(status_code=400, detail="路径不是目录")
        
        result = await knowledge_base_manager.add_directory(directory_path, recursive)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理目录失败: {str(e)}")


@router.get("/search")
async def search_knowledge_base(
    query: str = Query(..., description="搜索查询"),
    k: int = Query(5, ge=1, le=20, description="返回结果数量"),
    include_scores: bool = Query(False, description="是否包含相似度分数")
):
    """搜索知识库"""
    try:
        result = await knowledge_base_manager.search(query, k, include_scores)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/stats")
async def get_knowledge_base_stats():
    """获取知识库统计信息"""
    try:
        stats = knowledge_base_manager.get_knowledge_base_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.delete("/clear")
async def clear_knowledge_base():
    """清空知识库（谨慎使用）"""
    try:
        # 这里需要实现清空功能
        # 注意：这是一个危险操作，在生产环境中应该有更多的安全检查
        return {
            "success": False,
            "message": "清空功能暂未实现，请手动操作"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文件格式"""
    return {
        "supported_formats": list(knowledge_base_manager.doc_processor.supported_extensions.keys()),
        "description": "支持的文件格式列表"
    }
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高概率光子分析模块

该模块提供了使用srcprob方法找到概率大于指定阈值的最高能光子的功能。
主要用于伽马射线暴(GRB)分析中的高能光子识别和特征提取。

"""

import os
import numpy as np
import astropy.io.fits as pyfits
import pandas as pd
import threading
import logging
from astropy.coordinates import SkyCoord
import astropy.units as u

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_all_photons(events, prob_col, grb_name, grb_params, output_dir):
    """
    保存所有光子信息，包括概率和到达时间
    
    参数:
        events: FITS事件数据
        prob_col: 概率列名
        grb_name: GRB名称
        grb_params: GRB参数字典
        output_dir: 输出目录
    
    返回:
        str: 保存文件路径
    """
    try:
        thread_id = threading.current_thread().name
        logger.info(f"[{thread_id}] {grb_name} 开始保存所有光子信息...")
        
        # 检查输入参数
        if events is None:
            logger.error(f"[{thread_id}] {grb_name} events数据为None")
            return None
            
        if prob_col not in events.dtype.names:
            logger.error(f"[{thread_id}] {grb_name} 概率列 '{prob_col}' 不存在于events数据中")
            logger.error(f"[{thread_id}] {grb_name} 可用列名: {list(events.dtype.names)}")
            return None
            
        if 'trigger_met' not in grb_params:
            logger.error(f"[{thread_id}] {grb_name} grb_params中缺少trigger_met参数")
            return None
        
        logger.info(f"[{thread_id}] {grb_name} 事件总数: {len(events)}")
        logger.info(f"[{thread_id}] {grb_name} 使用概率列: {prob_col}")
        logger.info(f"[{thread_id}] {grb_name} 输出目录: {output_dir}")
        
        # 创建DataFrame保存所有光子信息
        all_photons_df = pd.DataFrame({
            'ENERGY': events['ENERGY'],
            'TIME': events['TIME'],
            'RELATIVE_TIME': events['TIME'] - grb_params['trigger_met'],  # 相对触发时间
            'PROBABILITY': events[prob_col],
            'RA': events['RA'],
            'DEC': events['DEC']
        })
        
        # 保存所有光子信息
        os.makedirs(output_dir, exist_ok=True)
        all_photons_file = os.path.join(output_dir, f"{grb_name}_all_photons.csv")
        all_photons_df.to_csv(all_photons_file, index=False)
        logger.info(f"[{thread_id}] {grb_name} 所有光子信息已保存: {all_photons_file}")
        logger.info(f"[{thread_id}] {grb_name} 保存的光子数量: {len(all_photons_df)}")
        
        return all_photons_file
    except Exception as e:
        thread_id = threading.current_thread().name
        logger.error(f"[{thread_id}] {grb_name} 保存所有光子信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def find_highest_prob_photon(gta, grb_name, grb_params, results_dir=None, prob_threshold=0.9):
    """
    使用srcprob方法找到概率大于指定阈值的最高能光子
    
    参数:
        gta: GTAnalysis对象，已完成拟合的Fermi分析对象
        grb_name: str, GRB名称
        grb_params: dict, GRB参数字典，包含ra, dec, trigger_met等
        results_dir: str, 结果保存目录，默认为None时使用当前目录
        prob_threshold: float, 概率阈值，默认0.9
    
    返回:
        dict: 包含最高能光子详细信息的字典，失败时返回None
              包含字段: energy, time, relative_time, ra, dec, 
                       angular_separation, probability, total_high_prob_photons,
                       event_class, event_type
    """
    try:
        thread_id = threading.current_thread().name
        logger.info(f"[{thread_id}] 正在计算 {grb_name} 的源概率...")
        
        # 计算源概率
        srcprob_result = gta.compute_srcprob()
        logger.info(f"[{thread_id}] {grb_name} 源概率计算完成")
        
        # 设置输出目录
        if results_dir is None:
            output_dir = os.getcwd()
        else:
            output_dir = os.path.join(results_dir, grb_name)
        
        # 查找srcprob文件
        srcprob_file = None
        
        # srcprob文件名
        srcprob_file = os.path.join(output_dir, 'ft1_srcprob_00.fits')
        
        if not os.path.exists(srcprob_file):
            logger.warning(f"[{thread_id}] {grb_name} 未找到srcprob文件: {srcprob_file}")
            return None
        
        logger.info(f"[{thread_id}] {grb_name} 找到srcprob文件: {srcprob_file}")
        
        # 读取srcprob文件
        with pyfits.open(srcprob_file) as hdul:
            events = hdul['EVENTS'].data
            
            # 检查可用的列名
            available_columns = list(events.dtype.names)
            logger.info(f"[{thread_id}] {grb_name} 可用列名: {available_columns}")
            
            # 查找GRB对应的概率列
            prob_col = grb_name
            if prob_col not in available_columns:
                # 尝试其他可能的列名
                possible_prob_cols = [col for col in available_columns if grb_name in col]
                if possible_prob_cols:
                    prob_col = possible_prob_cols[0]
                    logger.info(f"[{thread_id}] {grb_name} 使用概率列: {prob_col}")
                else:
                    logger.warning(f"[{thread_id}] {grb_name} 未找到对应的概率列")
                    return None
            
            # 保存所有光子信息
            try:
                all_photons_result = save_all_photons(events, prob_col, grb_name, grb_params, output_dir)
                if all_photons_result:
                    logger.info(f"[{thread_id}] {grb_name} 所有光子信息保存成功: {all_photons_result}")
                else:
                    logger.warning(f"[{thread_id}] {grb_name} 所有光子信息保存失败")
            except Exception as save_error:
                logger.error(f"[{thread_id}] {grb_name} 保存所有光子信息时出现异常: {str(save_error)}")
                import traceback
                traceback.print_exc()
            
            # 获取概率数据
            prob = events[prob_col]
            
            # 筛选概率大于阈值的高可信光子
            high_prob_mask = prob > prob_threshold
            high_prob_events = events[high_prob_mask]
            high_prob_probs = prob[high_prob_mask]
            
            logger.info(f"[{thread_id}] {grb_name} 共找到 {len(high_prob_events)} 个光子概率>{prob_threshold}")
            
            if len(high_prob_events) == 0:
                logger.warning(f"[{thread_id}] {grb_name} 未找到概率>{prob_threshold}的光子")
                return None
            
            # 在高概率光子中找到最高能量的光子
            max_energy_idx = np.argmax(high_prob_events['ENERGY'])
            highest_photon = high_prob_events[max_energy_idx]
            highest_prob = high_prob_probs[max_energy_idx]
            
            # 确保最高能量光子的概率大于0.9
            if highest_prob < 0.9:
                logger.warning(f"[{thread_id}] {grb_name} 最高能光子概率 {highest_prob:.4f} 小于0.9，寻找替代光子")
                # 筛选概率大于0.9的光子
                very_high_prob_mask = prob > 0.9
                very_high_prob_events = events[very_high_prob_mask]
                very_high_prob_probs = prob[very_high_prob_mask]
                
                if len(very_high_prob_events) == 0:
                    logger.warning(f"[{thread_id}] {grb_name} 未找到概率>0.9的光子")
                    return None
                
                # 在概率大于0.9的光子中找到最高能量的光子
                max_energy_idx = np.argmax(very_high_prob_events['ENERGY'])
                highest_photon = very_high_prob_events[max_energy_idx]
                highest_prob = very_high_prob_probs[max_energy_idx]
            
            # 计算相对于触发时间的时间
            relative_time = float(highest_photon['TIME']) - grb_params['trigger_met']
            
            # 计算与GRB位置的角距离
            grb_coord = SkyCoord(ra=grb_params['ra']*u.deg, dec=grb_params['dec']*u.deg)
            photon_coord = SkyCoord(ra=highest_photon['RA']*u.deg, dec=highest_photon['DEC']*u.deg)
            angular_separation = grb_coord.separation(photon_coord).degree
            
            # 安全地获取事件类型信息
            event_class = -1
            event_type = -1
            try:
                if 'EVENT_CLASS' in highest_photon.dtype.names:
                    event_class = int(highest_photon['EVENT_CLASS'])
                if 'EVENT_TYPE' in highest_photon.dtype.names:
                    event_type = int(highest_photon['EVENT_TYPE'])
            except:
                pass
            
            result = {
                'energy': float(highest_photon['ENERGY']),      # MeV
                'time': float(highest_photon['TIME']),          # MET
                'relative_time': relative_time,                 # 相对触发时间 (s)
                'ra': float(highest_photon['RA']),              # degrees
                'dec': float(highest_photon['DEC']),            # degrees
                'angular_separation': float(angular_separation), # degrees
                'probability': float(highest_prob),             # 源概率
                'total_high_prob_photons': len(high_prob_events), # 高概率光子总数
                'event_class': event_class,
                'event_type': event_type
            }
            
            logger.info(f"[{thread_id}] {grb_name} 最高能高概率光子:")
            logger.info(f"[{thread_id}] {grb_name}   能量: {result['energy']:.2f} MeV")
            logger.info(f"[{thread_id}] {grb_name}   概率: {result['probability']:.4f}")
            logger.info(f"[{thread_id}] {grb_name}   角距离: {result['angular_separation']:.4f}°")
            logger.info(f"[{thread_id}] {grb_name}   相对时间: {result['relative_time']:.2f} s")
            
            # 创建高概率光子的DataFrame用于详细分析
            df = pd.DataFrame({
                'ENERGY': high_prob_events['ENERGY'],
                'TIME': high_prob_events['TIME'],
                'RELATIVE_TIME': high_prob_events['TIME'] - grb_params['trigger_met'],  # 添加相对时间
                'PROB': high_prob_probs,
                'RA': high_prob_events['RA'],
                'DEC': high_prob_events['DEC']
            })
            
            # 保存高概率光子信息
            if results_dir:
                os.makedirs(output_dir, exist_ok=True)
                high_prob_file = os.path.join(output_dir, f"{grb_name}_high_prob_photons.csv")
                df.to_csv(high_prob_file, index=False)
                logger.info(f"[{thread_id}] {grb_name} 高概率光子信息已保存: {high_prob_file}")
            
            return result
            
    except Exception as e:
        thread_id = threading.current_thread().name
        logger.error(f"[{thread_id}] {grb_name} 使用srcprob方法获取最高能光子信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def analyze_high_prob_photons(gta, grb_name, grb_params, results_dir=None, prob_threshold=0.9, save_details=True):
    """
    分析所有高概率光子的统计信息
    
    参数:
        gta: GTAnalysis对象
        grb_name: str, GRB名称
        grb_params: dict, GRB参数
        results_dir: str, 结果保存目录
        prob_threshold: float, 概率阈值
        save_details: bool, 是否保存详细信息
    
    返回:
        dict: 包含统计信息的字典
    """
    try:
        # 首先获取最高能光子信息
        highest_photon = find_highest_prob_photon(gta, grb_name, grb_params, results_dir, prob_threshold)
        
        if highest_photon is None:
            return None
        
        # 这里可以添加更多的统计分析功能
        stats = {
            'highest_energy_photon': highest_photon,
            'total_high_prob_photons': highest_photon['total_high_prob_photons'],
            'prob_threshold': prob_threshold
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"分析高概率光子统计信息失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 示例用法
    print("高概率光子分析模块")
    print("主要功能:")
    print("1. find_highest_prob_photon() - 找到最高能的高概率光子")
    print("2. analyze_high_prob_photons() - 分析高概率光子统计信息")
    print("3. save_all_photons() - 保存所有光子信息")
    print("")
    print("使用方法:")
    print("from photon_analyzer import find_highest_prob_photon")
    print("result = find_highest_prob_photon(gta, grb_name, grb_params)")
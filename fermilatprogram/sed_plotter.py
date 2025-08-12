import matplotlib.pyplot as plt
import numpy as np

def plot_sed(c, sed, source_name='GRB250320B', show_plot=True, figsize=(10, 8)):
    """
    绘制SED图像
    
    参数:
    c: 拟合结果字典
    sed: SED数据
    source_name: 源名称
    show_plot: 是否显示图像
    figsize: 图像尺寸，默认(10, 8)
    
    返回:
    None
    """
    # 提取理论曲线数据
    E = np.array(c['sources'][source_name]['model_flux']['energies'])
    dnde = np.array(c['sources'][source_name]['model_flux']['dnde'])
    dnde_hi = np.array(c['sources'][source_name]['model_flux']['dnde_hi'])
    dnde_lo = np.array(c['sources'][source_name]['model_flux']['dnde_lo'])
    
    # 提取谱指数信息
    index = c['sources'][source_name]['spectral_pars']['Index']['value']
    index_err = c['sources'][source_name]['spectral_pars']['Index']['error']
    
    # 清除之前的图像并设置画布大小
    plt.figure(figsize=figsize)
    plt.clf()
    
    # 绘制理论曲线
    plt.loglog(E, (E**2)*dnde, 'k--')
    plt.loglog(E, (E**2)*dnde_hi, 'k', alpha=0.5)
    plt.loglog(E, (E**2)*dnde_lo, 'k', alpha=0.5)
    
    # 识别上限点 (dnde_err_lo为NaN的点)
    mask_ul = np.isnan(sed['dnde_err_lo'])
    sed['e2dnde'] = np.where(mask_ul, sed['e2dnde_ul95'], sed['e2dnde'])
    
    # 分离检测点和上限点
    detected = ~mask_ul  # 检测到的点
    upper_limits = mask_ul  # 上限点
    
    # 计算x轴误差
    xerr = np.array([
        sed['e_ctr'] - sed['e_min'],  # 左误差
        sed['e_max'] - sed['e_ctr']   # 右误差
    ])
    
    # 绘制检测点（带双侧误差棒和T型帽）
    if np.any(detected):
        plt.errorbar(sed['e_ctr'][detected], 
                     sed['e2dnde'][detected], 
                     yerr=sed['e2dnde_err'][detected], 
                     xerr=xerr[:, detected],
                     fmt='o', 
                     color='black', 
                     capsize=3,  # 添加T型帽，capsize控制帽的长度
                    #  label='Detected'
                     )
    
    # 绘制上限点（带向上箭头）
    if np.any(upper_limits):
        plt.errorbar(sed['e_ctr'][upper_limits], 
                     sed['e2dnde'][upper_limits], 
                     xerr=xerr[:, upper_limits],
                     yerr=0.3 * sed['e2dnde'][upper_limits],  # 小偏移使箭头可见
                     uplims=True,  # 显示为上限
                     fmt='none',   # 不显示数据点标记
                     color='black',
                     capsize=3,    # 添加T型帽
                    #  label='Upper limits'
                     )
    
    # 添加谱指数信息
    plt.gca().text(0.98, 0.98, f"Index: {index:.2f} ± {index_err:.2f}", 
                   transform=plt.gca().transAxes, 
                   ha='right', 
                   va='top', 
                   fontsize=10, 
                   bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    
    # 动态计算y轴上限
    # 考虑所有数据点：检测点+误差、上限点
    max_values = []
    
    # 检测点的最大值（数据点+误差）
    if np.any(detected):
        detected_max = np.nanmax(sed['e2dnde'][detected] + sed['e2dnde_err'][detected])
        max_values.append(detected_max)
    
    # 上限点的最大值
    if np.any(upper_limits):
        ul_max = np.nanmax(sed['e2dnde_ul95'][upper_limits])
        max_values.append(ul_max)
    
    # 设置y轴上限为最大值的1.5倍，确保所有数据都可见
    if max_values:
        y_max = max(max_values) * 1.5
    else:
        y_max = 1e-2  # 默认值
    
    # 动态计算y轴上限
    # 考虑所有数据点：检测点+误差、上限点
    max_values = []
    
    # 检测点的最大值（数据点+误差）
    if np.any(detected):
        detected_max = np.nanmax(sed['e2dnde'][detected] + sed['e2dnde_err'][detected])
        max_values.append(detected_max)
    
    # 上限点的最大值
    if np.any(upper_limits):
        ul_max = np.nanmax(sed['e2dnde_ul95'][upper_limits])
        max_values.append(ul_max)
    
    # 设置y轴上限为最大值的1.5倍，确保所有数据都可见
    if max_values:
        y_max = max(max_values) * 1.5
    else:
        y_max = 1e-2  # 默认值
    
    # 设置坐标轴
    plt.xlim(1e2, 1e5)
    plt.ylim(bottom=1e-5, top=y_max)
    plt.xlabel('E [MeV]')
    plt.ylabel(r'E$^{2}$ dN/dE [MeV cm$^{-2}$ s$^{-1}$]')
    plt.legend()  # 显示图例区分点类型
    
    if show_plot:
        plt.show()

def save_sed_plot(c, sed, source_name='GRB250320B', filename=None, figsize=(10, 8)):
    """
    保存SED图像到文件
    
    参数:
    c: 拟合结果字典
    sed: SED数据
    source_name: 源名称
    filename: 保存文件名，如果为None则使用默认名称
    figsize: 图像尺寸，默认(10, 8)
    
    返回:
    保存的文件路径
    """
    plt.figure(figsize=figsize)
    plot_sed(c, sed, source_name, show_plot=False)
    
    if filename is None:
        filename = f"{source_name.lower()}_sed.png"
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filename
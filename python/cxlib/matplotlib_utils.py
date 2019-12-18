from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

def savefigMultipage(filename, figs=None):
    pp = PdfPages(filename)
    if figs is None:
        figs = [plt.figure(n) for n in plt.get_fignums()]
    for fig in figs:
        fig.savefig(pp, format='pdf', dpi=fig.dpi)
    pp.close()

def gridShow(nCol = 2):
    for idx, idFig in enumerate(plt.get_fignums()):
        plt.figure(idFig)
        mgr = plt.get_current_fig_manager()
        arg = "+%i+%i" % (idx % nCol * 700, int(idx/nCol) * 500)
        mgr.window.wm_geometry(arg)

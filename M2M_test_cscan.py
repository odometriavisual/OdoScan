from array import *
from numpy import *
from numpy.random import *
from math import *
from M2M_Remote_lib import *
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

class RealTimeCScan:
    def __init__(self, ip="127.0.0.1", remote_port=4444, data_port=4445):
        """
        Inicializa o sistema M2M e configurações de visualização
        """
        self.m2m_system = M2k_system()
        self.m2m_system.set_ip(ip, remote_port)
        self.m2m_system.set_ip_data_server(ip, data_port)
        
        # Buffers para armazenar dados
        self.cscan_data = None
        self.position_index = 0
        self.max_positions = 20  # Número máximo de posições a armazenar
        self.buffer_full = False  # Flag para indicar se o buffer já foi preenchido uma vez
        
        # Configurações de visualização
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.im = None
        
        # Estatísticas
        self.frame_count = 0
        self.start_time = None
        self.fps_text = None
        
    def connect(self):
        """Conecta ao sistema M2M"""
        print("Conectando ao M2M...")
        self.m2m_system.connect()
        
        # Atualiza parâmetros do sistema
        print("Atualizando parâmetros...")
        self.m2m_system.update_all_parameters(with_focal_laws=False, with_dac_curves=False)
        
        print(f"Conexão estabelecida!")
        print(f"Configuração: {self.m2m_system.NameOfTheConfiguration}")
        print(f"Número de salvos: {self.m2m_system.Nb_Salvos}")
        
    def get_ascan_data(self):
        """
        Captura dados de A-scan do sistema
        Retorna array com dados brutos
        """
        try:
            # Captura todos os A-scans
            ascan_raw = M2K_Get_All_Ascans(self.m2m_system.socket)
            return ascan_raw
        except Exception as e:
            print(f"Erro ao capturar A-scan: {e}")
            return None
    
    def process_ascan_to_cscan(self, ascan_data):
        """
        Processa dados de A-scan para gerar linha do C-scan
        Extrai tempo de voo máximo (pico) de cada canal
        """
        if ascan_data is None or len(ascan_data) == 0:
            return None
        
        print(ascan_data.shape)
        # Para cada A-scan, encontra o índice do pico máximo
        # Isso representa o tempo de voo
        peak_times = np.argmax(ascan_data, axis=1)
        
        # Ou podemos usar a amplitude máxima
        peak_amplitudes = np.max(ascan_data, axis=1)
        
        # Retorna amplitudes (pode ser alterado para peak_times se preferir tempo de voo)
        return peak_amplitudes
    
    def initialize_cscan_buffer(self, num_channels):
        """Inicializa buffer do C-scan"""
        self.cscan_data = np.zeros((num_channels, self.max_positions))
        print(f"Buffer C-scan inicializado: {self.cscan_data.shape}")
    
    def update_cscan(self, new_line):
        """Adiciona nova linha ao buffer circular."""
        if self.cscan_data is None:
            self.initialize_cscan_buffer(len(new_line))
            self.position_index = 0
            self.buffer_full = False

        # Adiciona nova linha na posição atual
        self.cscan_data[:, self.position_index] = new_line
        
        # Avança o índice
        self.position_index += 1
        
        # Verifica se completou o buffer pela primeira vez
        if self.position_index >= self.max_positions:
            self.buffer_full = True
            self.position_index = 0  # Volta ao início (roll)

    def get_valid_cscan_data(self):
        """Retorna a visão correta dos dados para visualização."""
        if self.cscan_data is None:
            return None
            
        if not self.buffer_full:
            # Buffer ainda não preencheu completamente
            return self.cscan_data[:, :self.position_index]
        else:
            # Buffer completo - reorganiza para mostrar em ordem cronológica
            # A ordem correta é: da posição atual até o final, depois do início até posição atual
            return np.hstack([
                self.cscan_data[:, self.position_index:],
                self.cscan_data[:, :self.position_index]
            ])
    
    def setup_plot(self):
        """Configura visualização matplotlib"""
        self.ax.set_title('C-Scan em Tempo Real', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Posição de Scanning')
        self.ax.set_ylabel('Canal / Elemento')
        
        # Texto para FPS
        self.fps_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                     verticalalignment='top', color='white',
                                     bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        plt.tight_layout()
    
    def update_plot(self, frame):
        """Atualiza plot a cada frame"""
        # Captura novos dados
        ascan_data = self.get_ascan_data()
        
        if ascan_data is not None:
            # Processa A-scan para linha do C-scan
            cscan_line = self.process_ascan_to_cscan(ascan_data)
            
            if cscan_line is not None:
                # Atualiza buffer do C-scan
                self.update_cscan(cscan_line)
                
                # Obtém dados válidos para visualização
                valid_data = self.get_valid_cscan_data()
                
                if valid_data is None or valid_data.shape[1] == 0:
                    return []
                
                # Atualiza imagem
                if self.im is None:
                    # Primeira vez: cria imagem
                    self.im = self.ax.imshow(valid_data, aspect='auto', 
                                            cmap='jet', interpolation='nearest',
                                            origin='lower')
                    plt.colorbar(self.im, ax=self.ax, label='Amplitude')
                else:
                    # Atualiza dados da imagem existente
                    self.im.set_data(valid_data)
                    self.im.set_extent([0, valid_data.shape[1], 0, valid_data.shape[0]])
                    
                    # Atualiza escala de cores
                    self.im.set_clim(vmin=valid_data.min(), vmax=valid_data.max())
                
                # Atualiza FPS
                self.frame_count += 1
                if self.start_time is None:
                    self.start_time = time.time()
                
                elapsed = time.time() - self.start_time
                if elapsed > 0:
                    fps = self.frame_count / elapsed
                    total_positions = self.max_positions if self.buffer_full else self.position_index
                    self.fps_text.set_text(f'FPS: {fps:.1f}\nPosições: {total_positions}/{self.max_positions}')
        
        return [self.im, self.fps_text] if self.im else []
    
    def run(self, interval=50):
        """
        Executa visualização em tempo real
        interval: intervalo de atualização em ms
        """
        try:
            # Conecta e configura
            self.connect()
            
            # Configura plot
            self.setup_plot()
            
            # Aguarda estabilização
            time.sleep(1)
            
            # Configura animação
            print(f"Iniciando visualização (intervalo: {interval}ms)...")
            anim = FuncAnimation(self.fig, self.update_plot, 
                               interval=interval, blit=True, cache_frame_data=False)
            
            plt.show()
            
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário")
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Limpa recursos
            self.m2m_system.disconnect()
            print("Desconectado.")
    
    def save_cscan(self, filename="cscan_data.npy"):
        """Salva dados do C-scan em arquivo"""
        if self.cscan_data is not None:
            valid_data = self.get_valid_cscan_data()
            np.save(filename, valid_data)
            print(f"C-scan salvo em: {filename}")
            
            # Também salva como imagem
            plt.figure(figsize=(10, 8))
            plt.imshow(valid_data, aspect='auto', cmap='jet', interpolation='nearest', origin='lower')
            plt.colorbar(label='Amplitude')
            plt.title('C-Scan Capturado')
            plt.xlabel('Posição de Scanning')
            plt.ylabel('Canal / Elemento')
            plt.tight_layout()
            plt.savefig(filename.replace('.npy', '.png'), dpi=300)
            print(f"Imagem salva em: {filename.replace('.npy', '.png')}")


def main():
    """Função principal"""
    # Cria instância do visualizador
    viewer = RealTimeCScan(ip="127.0.0.1", remote_port=4444, data_port=4445)
    
    # Executa visualização
    # interval: tempo entre frames em ms (menor = mais rápido, mas mais CPU)
    viewer.run(interval=0)  # Atualiza o mais rápido possível
    
    # Salva dados ao finalizar
    #viewer.save_cscan("cscan_realtime.npy")


if __name__ == '__main__':
    main()
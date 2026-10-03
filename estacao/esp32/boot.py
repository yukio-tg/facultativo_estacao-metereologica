# Este arquivo roda sozinho sempre que a placa recebe energia ou é reiniciada.
# Ele não pode entrar em loop: ao terminar, o MicroPython executa main.py.

import esp

esp.osdebug(None)
print("Alimentação detectada. Iniciando a estação...")

from unidecode import unidecode
from collections import defaultdict
from itertools import product

# Configurações
MAX_TEXT_LEN = 10000
MIN_PATTERN_LEN = 2
MAX_PATTERN_LEN = 5
MAX_KEY_CANDIDATES = 40
CORRELATION_THRESHOLD = 0.98
MAX_KEYS_TO_GENERATE = 100

# Tabelas de frequência
FREQ_PORTUGUES = [
    14.63, 0.40, 3.88, 4.99, 12.57, 1.02, 1.30, 1.28, 6.18, 0.40, 0.02, 2.78,
    4.74, 4.78, 10.73, 2.52, 1.20, 6.53, 7.81, 4.34, 4.63, 1.67, 0.21, 0.02,
    0.47, 0.00]

FREQ_INGLES = [
    8.20, 1.49, 2.78, 4.25, 12.70, 2.23, 2.02, 6.09, 6.97, 0.15, 0.77, 4.03,
    2.41, 6.75, 7.50, 1.93, 0.10, 5.99, 6.33, 9.10, 2.76, 0.98, 2.36, 0.15,
    1.97, 0.05]


def mostrar_menu():
    print("\n=== Ferramenta de Cifra de Vigenère ===")
    print("1. Criptografar texto")
    print("2. Descriptografar texto")
    print("3. Quebrar cifra")
    print("4. Sair")
    return input("Digite sua escolha: ")


def normalizar_caractere(c):
    """Remove acentos e converte para maiúsculas"""
    return unidecode(c).upper()


def processar_chave(chave):
    """Filtra e normaliza caracteres da chave"""
    return ''.join([c for c in (normalizar_caractere(char) for char in chave) if c.isalpha()])


def deslocar_caractere(c, deslocamento, criptografar=True):
    """Desloca um caractere mantendo maiúsculas"""
    if not c.isalpha():
        return ''

    base = ord('A')
    offset = ord(c) - base
    modificado = (offset + deslocamento) % 26 if criptografar else (offset - deslocamento) % 26
    return chr(base + modificado)


def criptografar_vigenere(texto_plano, chave):
    """Criptografa texto ignorando caracteres não-alfabéticos"""
    chave_processada = processar_chave(chave)
    if not chave_processada:
        raise ValueError("A chave deve conter pelo menos uma letra")

    texto_limpo = [normalizar_caractere(c) for c in texto_plano if normalizar_caractere(c).isalpha()]
    tamanho_chave = len(chave_processada)
    texto_cifrado = []

    for i, c in enumerate(texto_limpo):
        deslocamento = ord(chave_processada[i % tamanho_chave]) - ord('A')
        texto_cifrado.append(deslocar_caractere(c, deslocamento))

    return ''.join(texto_cifrado)


def descriptografar_vigenere(texto_cifrado, chave):
    """Descriptografa texto ignorando caracteres não-alfabéticos"""
    chave_processada = processar_chave(chave)
    if not chave_processada:
        raise ValueError("A chave deve conter pelo menos uma letra")

    texto_limpo = [normalizar_caractere(c) for c in texto_cifrado if normalizar_caractere(c).isalpha()]
    tamanho_chave = len(chave_processada)
    texto_plano = []

    for i, c in enumerate(texto_limpo):
        deslocamento = ord(chave_processada[i % tamanho_chave]) - ord('A')
        texto_plano.append(deslocar_caractere(c, deslocamento, False))

    return ''.join(texto_plano)


def limpar_texto(texto):
    """Remove todos os caracteres não-alfabéticos"""
    return ''.join([normalizar_caractere(c) for c in texto if normalizar_caractere(c).isalpha()])


def encontrar_repeticoes(texto):
    """Encontra sequências repetidas no texto"""
    distancias = []
    texto = limpar_texto(texto)
    tamanho_texto = len(texto)

    for tamanho_padrao in range(MIN_PATTERN_LEN, MAX_PATTERN_LEN + 1):
        for i in range(tamanho_texto - tamanho_padrao + 1):
            padrao = texto[i:i + tamanho_padrao]
            j = i + tamanho_padrao
            while j + tamanho_padrao <= tamanho_texto:
                if texto[j:j + tamanho_padrao] == padrao:
                    distancias.append(j - i)
                j += 1
    return distancias


def fatorar_distancias(distancias):
    """Fatora as distâncias encontradas"""
    fatores = []
    for d in distancias:
        for f in range(2, d + 1):
            if d % f == 0:
                fatores.append(f)
    return fatores


def coletar_tamanhos_chave(fatores):
    """Encontra os fatores mais comuns"""
    contagem_fatores = defaultdict(int)
    for f in fatores:
        contagem_fatores[f] += 1

    if not contagem_fatores:
        return []

    max_contagem = max(contagem_fatores.values())
    candidatos = [f for f, contagem in contagem_fatores.items() if contagem == max_contagem]
    return sorted(candidatos, reverse=True)[:MAX_KEY_CANDIDATES]


def gerar_chaves(texto, tamanho_chave, tabela_freq):
    """Gera possíveis chaves usando análise de frequência"""
    texto = limpar_texto(texto)
    possibilidades = [[] for _ in range(tamanho_chave)]

    for pos in range(tamanho_chave):
        freq = [0] * 26
        total = 0

        for i in range(pos, len(texto), tamanho_chave):
            freq[ord(texto[i]) - ord('A')] += 1
            total += 1

        if total == 0:
            continue

        correlacoes = []
        for deslocamento in range(26):
            pontuacao = sum((freq[(c + deslocamento) % 26] / total * 100) * tabela_freq[c] for c in range(26))
            correlacoes.append((deslocamento, pontuacao))

        max_pontuacao = max(correlacoes, key=lambda x: x[1])[1]
        limite = max_pontuacao * CORRELATION_THRESHOLD
        melhores = [s for s, p in correlacoes if p >= limite]
        possibilidades[pos] = melhores or [max(correlacoes, key=lambda x: x[1])[0]]

    chaves = []
    for combinacao in product(*possibilidades):
        chave = ''.join([chr(ord('A') + s) for s in combinacao])
        chaves.append(chave)
        if len(chaves) >= MAX_KEYS_TO_GENERATE:
            break

    return chaves


def quebrar_cifra(texto_cifrado, tabela_freq, idioma):
    """Processo completo de quebra de cifra"""
    texto_limpo = limpar_texto(texto_cifrado)
    print(f"\nProcessando cifra em {idioma} ({len(texto_limpo)} caracteres)")

    distancias = encontrar_repeticoes(texto_limpo)
    fatores = fatorar_distancias(distancias)
    tamanhos_chave = coletar_tamanhos_chave(fatores)

    print(f"Possíveis tamanhos de chave: {tamanhos_chave[:MAX_KEY_CANDIDATES]}")

    for tam in tamanhos_chave[:3]:
        chaves = gerar_chaves(texto_limpo, tam, tabela_freq)
        print(f"\nChaves de tamanho {tam} ({len(chaves)} encontradas):")
        for chave in chaves[:5]:
            decifrado = descriptografar_vigenere(texto_cifrado, chave)
            print(f"{chave} -> {decifrado[:60]}{'...' if len(decifrado) > 60 else ''}")


def main():
    while True:
        escolha = mostrar_menu()

        if escolha == '1':
            texto = input("Digite o texto para criptografar: ")
            chave = input("Digite a chave de criptografia: ")
            try:
                cifrado = criptografar_vigenere(texto, chave)
                print(f"\nTexto criptografado: {cifrado}")
            except ValueError as e:
                print(f"Erro: {e}")

        elif escolha == '2':
            texto = input("Digite o texto para descriptografar: ")
            chave = input("Digite a chave de descriptografia: ")
            try:
                decifrado = descriptografar_vigenere(texto, chave)
                print(f"\nTexto descriptografado: {decifrado}")
            except ValueError as e:
                print(f"Erro: {e}")

        elif escolha == '3':
            texto = input("Digite o texto cifrado para quebrar: ")
            idioma = input("Selecione o idioma (1-Português, 2-Inglês): ")

            if idioma == '1':
                quebrar_cifra(texto, FREQ_PORTUGUES, "Português")
            elif idioma == '2':
                quebrar_cifra(texto, FREQ_INGLES, "Inglês")
            else:
                print("Escolha de idioma inválida!")

        elif escolha == '4':
            print("Saindo...")
            break

        else:
            print("Escolha inválida!")


if __name__ == "__main__":
    main()

# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

import os
import shutil
import tarfile
import sys
import zipfile
import subprocess
from . import apkforge
from .logger import logger
from .exceptions import APKVoltError
import py_compile

# libs_supported.py
SUPPORTED_LIBS = [
	"kivy", "kivymd", "plyer", "pyjnius", "requests", "websockets",
	"tinydb", "pillow", "qrcode", "passlib", "numpy",
	"python-dateutil", "pytz", "loguru", "native-libs"
]

# Confirma a existencia do python 3.11 utilizavel
python311_confirm = False

# Verifica se a versao do python do runtime eh 3.11
if sys.version_info[:2] == (3, 11):
	# Se for, nao sera necessario o uso de python externo
	PYTHON311_PATH = None
	python311_confirm = True
else:
	# Lista de possiveis chamadas do python3.11
	python_calls = ["python3.11", "python311", "python", "python3"]
	# Define o caminho do python3.11 como None
	PYTHON311_PATH = None
	# Percorre cada possivel chamada do python3.11
	for pycall in python_calls:
		# Verifica se existe no path
		if shutil.which(pycall) is not None:
			# Solicita a versao
			result = subprocess.run(
				[
					pycall,
					"-c",
					"import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"
				],
				capture_output=True,
				text=True
			)
			if result.stdout.strip() == "3.11":
				# Define o caminho do python3.11 como o encontrado
				PYTHON311_PATH = shutil.which(pycall)
				python311_confirm = True
				# Quebra o loop de chamadas
				break

# Empacota o cache em private.tar
def cache_to_tar(path):
	cache_dir = os.path.join(path, '.apkvolt_cache') # Caminho do cache
	output_tar = os.path.join(cache_dir, 'private.tar') # Caminho onde vai ser feito o private.tar, eh feito onde o comando foi chamado
	
	# Cria e abre o private.tar
	with tarfile.open(output_tar, "w:gz", compresslevel=9) as tar:
		
		# Percorre todos os itens do cache
		for item in os.listdir(cache_dir):
			item_path = os.path.join(cache_dir, item)
			# arcname=item garante que os arquivos fiquem na raiz do tar, sem o caminho completo
			tar.add(item_path, arcname=item)

# Funcao para empacotar cache em apk
def  cache_to_apk(
	cache_path, # Caminho do cache que sera empacotado em apk
	output_apk, # Caminho onde o aplicativo sera gerado
	app_name=None, # Nome do aplicativo
	app_version_code=None, # Codigo da versao do aplicativo
	app_version_name=None, # Versao legivel do aplicativo
	min_sdk_version=21, # Versao minima do sdk exigida pelo app
	target_sdk_version=34, # Versao alvo do sdk preferida pelo app):
	package=None, # Package do app
	icon=None, # Icone principal do app
	icon_background=None, # Icone de fundo do app
	icon_foreground=None, # Icone de primeiro plano do app
	presplash=None, # Imagem que parece na tela de carregamento
	):
	
	# Obtem o diretorio com o script atual
	script_path = os.path.realpath(__file__)

	# Obtem o diretório onde o script esta
	script_dir = os.path.dirname(script_path)
	
	# Caminho da pasta de apk templates
	apk_base_dir = os.path.join(script_dir, 'apkvolt_apk_base')
	private_path = os.path.join(cache_path, 'private.tar')
	
	# Pega o caminho completo do primeiro apk template
	for file in os.listdir(apk_base_dir):
		if file.lower().endswith('.apk'):
			apk_base_path = os.path.join(apk_base_dir, file)
			break
			
	# Lista de arquivos que podem ser modificados
	new_apk_files = [
		"assets/private.tar",
		"res/drawable/presplash.png",
		"resources.arsc",
		"AndroidManifest.xml",
		"classes.dex"
	]
	new_apk_files_path = [
		private_path,
		os.path.join(cache_path, 'res/drawable/presplash.png'),
		os.path.join(cache_path, 'resources.arsc'),
		os.path.join(cache_path, 'AndroidManifest.xml'),
		os.path.join(cache_path, 'classes.dex')
	]
	
	# Abre o apk template e o apk resultante
	with zipfile.ZipFile(apk_base_path, 'r') as apk_zip_temp, zipfile.ZipFile(output_apk, 'w') as apk_zip:
		# Percorre todos os itens dentro do apk template
		for item in apk_zip_temp.infolist():
			# Se o arquivo nao estiver na lista dos que podem ser modificados (incluindo todos os icones mipmap)
			if item.filename not in new_apk_files and ((not item.filename.startswith("res/mipmap-") and not item.filename.endswith("dpi-v4")) or item.filename.startswith("res/mipmap-anydpi-v26")):
				# Copia os arquivos do apk template para o apk resultante
				apk_zip.writestr(item, apk_zip_temp.read(item.filename))
			else:
				if item.filename != "assets/private.tar":
					apk_zip_temp.extract(item.filename, cache_path) # Extrai para o cache tudo aquilo que nao for o private.tar
		
		# Gera a arvore de icones em diferentes dimensoes apartir da dpi
		apkforge.generate_asset(ic_launcher=icon, ic_launcher_background=icon_background, ic_launcher_foreground=icon_foreground, presplash=presplash, output=cache_path)
		
		# Percorre todos os icones de todas as dpi's'
		# Percorre todas as dpi's do dicionario icon_sizes
		for dpi in list(apkforge.icon_sizes.keys()):
				# Percorre todos os nomes de icones do dicionario icon_sizes
				for icon_name in list(apkforge.icon_sizes[dpi].keys()):
					apk_file = f"res/mipmap-{dpi}-v4/{icon_name}.png"
					apk_file_path = os.path.join(cache_path, apk_file)
					
					# Armazena as propriedades do arquivo que sera adicionado ao apk
					info = zipfile.ZipInfo(apk_file)
					# Define o metodo de compreensao, para comprimir e diminuir o tamanho
					info.compress_type = zipfile.ZIP_STORED
					
					
					# Abre e le o arquivo que sera adicionado ao apk
					with open(apk_file_path, 'rb') as file:
						file_data = file.read()
						
					# Adiciona o arquivo ao apk com as propriedades adequadas
					apk_zip.writestr(info, file_data)
					
					
		
		# Percorre todos os arquivos que seram adicionados no apk
		for i in range(len(new_apk_files)):
			apk_file = new_apk_files[i]
			apk_file_path = new_apk_files_path[i]
			
			# Armazena as propriedades do arquivo que sera adicionado ao apk
			info = zipfile.ZipInfo(apk_file)
			# Define o metodo de compreensao, para comprimir e diminuir o tamanho
			info.compress_type = zipfile.ZIP_DEFLATED
			
			# Se nao for o private.tar
			if apk_file != "assets/private.tar":
				# Define o metodo de compreensao, para nao comprimir devido as exigencias do android
				info.compress_type = zipfile.ZIP_STORED
			
			### Os if's a seguir sao tratamentos especiais para cada arquivo'
				
			# Se for o classes.dex
			if apk_file == "classes.dex":
				dex_object = apkforge.DEX(apk_file_path) # Abre o arquivo dex
				if package: # Se um package foi especificado
					dex_object.set_package(0, package) # Altera do package do dex
				dex_object.save() # Salva as alteracoes
				dex_object.close() # Fecha o dex
			# Se for o resource.arsc
			if apk_file == "resources.arsc":
				arsc_object = apkforge.ARSC(apk_file_path) # Abre o arquivo arsc
				if app_name != None: # Se um nome foi especificado
					arsc_object.set_string_res(0x7f050000, app_name) # Muda o nome do app dentro do arsc
				if package: # Se um package foi especificado
					arsc_object.set_package(0x7f, package) # Altera do package do dex
				arsc_object.save() # Salva as alteracoes
			if apk_file == "AndroidManifest.xml":
				
				axml_object = apkforge.AXML(apk_file_path) # Abre o arquivo axml
				if package: # Se um package foi especificado
					axml_object.set_string_attribute('package', package) # Altera do package do axml
				if app_version_name != None: # Se uma versao legivel foi especificada
					axml_object.set_string_attribute('versionName', str(app_version_name)) # Muda a versao legivel do app dentro do AndroidManifest.xml
					
				if app_version_code != None: # Se uma versao numerica foi especificada
					axml_object.set_int_attribute('versionCode', app_version_code) # Muda a versaonumerica do app dentro do AndroidManifest.xml
					
				if min_sdk_version != None: # Se uma versao minima do sdk foi especificada
					axml_object.set_int_attribute('minSdkVersion', min_sdk_version) # Muda a versao minima do sdk dentro do AndroidManifest.xml
				if target_sdk_version != None: # Se uma versao alvo do sdk foi especificada
					axml_object.set_int_attribute('targetSdkVersion', target_sdk_version) # Muda a versao alvo do sdk dentro do AndroidManifest.xml
					
				axml_object.save() # Salva o axml modificado
				
			# Abre e le o arquivo que sera adicionado ao apk
			with open(apk_file_path, 'rb') as file:
				file_data = file.read()
			# Adiciona o arquivo ao apk com as propriedades adequadas
			apk_zip.writestr(info, file_data)

# Funcao para compilar projeto python em apk
def build(
	path, # diretorio que ser compilado
	keystore_path=None, # Caminho do keystore
	key_alias=None, # Alias da keystore
	keystore_pass=None, # Senha da keystore
	key_pass=None, # Senha da chave da keystore
	apk_sign=False, # Se o apk sera assinado (False ou True)
	app_name=None, # Nome do aplicativo
	app_version_code=10211, # Codigo da versao do aplicativo
	app_version_name='0.1', # Versao legivel do aplicativo
	min_sdk_version=21, # Versao minima do sdk exigida pelo app
	target_sdk_version=34, # Versao alvo do sdk preferida pelo app
	package=None, # Package do app
	icon=None, # Icone principal do app
	icon_background=None, # Icone de fundo do app
	icon_foreground=None, # Icone de primeiro plano do app
	presplash=None, # Imagem que parece na tela de carregamento
	output=None # Nome do apk gerado
	):
	# Emite um erro se o caminho nao existir
	if not os.path.exists(path):
		logger.error("Path not found")
		raise APKVoltError(f"Path not found: {path}")
	
	if apk_sign:
		# Emite um erro se o caminho da keystore nao for especificado
		if keystore_path is None:
			logger.error("Keystore path not specified")
			raise APKVoltError("Keystore path not specified")
		# Emite um erro se o caminho da keystore nao existir
		if not os.path.exists(keystore_path):
			logger.error("Keystore path not found")
			raise APKVoltError(f"Keystore path not found: {keystore_path}")
		if key_alias is None:
			logger.error("Key alias not specified")
			raise APKVoltError("Key alias not specified")
		
	# Obtem o diretorio com o script atual
	script_path = os.path.realpath(__file__)

	# Obtem o diretório onde o script esta
	script_dir = os.path.dirname(script_path)
	
	cache_path = os.path.join(path, '.apkvolt_cache') # Caminho da pasta de cache
	
	if not output: # Se nenhum nome foi informado, um nome eh gerado
		output = 'APKVolt_App.apk' 
		
	output_apk = os.path.join(os.getcwd(), output) # Caminho do apk resultante
	
	
	# Caminho completo do template do private.tar
	private_base_path = os.path.join(script_dir, 'apkvolt_private_base')
	
	# Caminho completo do template do apk
	apk_base_path = os.path.join(script_dir, 'apkvolt_apk_base')
	
	output_apk_cache = os.path.join(cache_path, 'apkvolt_app.apk') # Caminho do apk temporario
	
	# Deleta o apk antigo se existir
	if os.path.exists(output_apk):
		os.remove(output_apk)
		
	# Deleta o cache se existir
	if os.path.exists(cache_path):
		shutil.rmtree(cache_path)
	
	logger.info("Creating compiled cache")
	
	# Cria a pasta de cache
	os.mkdir(cache_path)
	
	# Percorre todos os arquivos no diretorio a ser compilado
	for raw_dir, subdir, files in os.walk(path):
		for file in files:
			# Separa o caminho do path
			dir = os.path.relpath(raw_dir, path)
			dir_file = os.path.join(dir, file) # Caminho superficial do arquivo a ser compilado
			path_dir_file = os.path.join(path, dir_file) # Caminho completo do arquivo a ser compilado
			path_cache_subdir = os.path.join(path, '.apkvolt_cache/', dir) # Caminho completo de pastas dentro do cache
			path_cache_subdir_file = os.path.join(path, '.apkvolt_cache/', dir, file) # Caminho completo de um arquivo dentro de pastas dentro do cache
			# Se nao for um arquivo do cache ou do private template
			if not '.apkvolt_cache' in dir_file and not 'apkvolt_private_base' in dir_file:
				if not os.path.exists(path_cache_subdir):
					# Cria as pastas do cache
					os.makedirs(path_cache_subdir, exist_ok=True)
				# Copia os arquivos a ser compilados pro cache
				shutil.copy2(path_dir_file, path_cache_subdir)
				# Compila o arquivo em pyc se for um script python
				if file[-3:] == '.py':
					
					# Define o nome do arquivo python compilado (sendo o mesmo nome porem com 'c' no final, resultando em '.pyc' na extensao)
					out = path_cache_subdir_file+'c'
					
					# Se nao encontrar um python3.11
					if not python311_confirm:
						# Emite um erro com instrucoes
						logger.error("No valid Python 3.11 runtime found")
						raise APKVoltError(
							"APKVolt requires a Python 3.11 runtime.\n"
							"It can be either:\n"
							"- the current interpreter (sys.version == 3.11), or\n"
							"- an external python3.11 available in PATH.\n"
						)
		
					# Se o um python externo nao foi especificado significa que a versao do python do runtime ja eh 3.11
					if PYTHON311_PATH is None:
						# Compila no python do proprio runtime
						py_compile.compile(r"{path_cache_subdir_file}", cfile=r"{out}", doraise=True)
					else:
						# O codigo para compilar o py em pyc, que sera utilizado no python3.11 encontrado
						code = f"""
import py_compile
py_compile.compile(r"{path_cache_subdir_file}", cfile=r"{out}", doraise=True)
"""
						# O comando para chamar o python3.11 externo e rodar o codigo
						cmd = [
							PYTHON311_PATH,
							"-c",
							code
						]
						
						# Executa o comando para chamar o python3.11 e compilar o py em pyc
						subprocess.run(cmd, check=True)
					
					# Apaga o arquivo nao compilado
					os.remove(path_cache_subdir_file)

	# Copia os arquivos necessarios pro private.tar
	for dir, subdir, files in os.walk(private_base_path):
		for file in files:
			dir_file = os.path.join(dir, file) # Caminho superficial do arquivo a ser compilado
			shutil.copy2(dir_file, cache_path)
	
	logger.success("Cache created")
	logger.info("Packing cache")
	
		
	cache_to_tar(path) # Compacta os arquivos do cache em private.tar
	
	logger.success("private.tar created")
	
	logger.info("Packing apk")
	
	cache_to_apk(
		cache_path,
		output_apk,
		app_name=app_name,
		app_version_code=app_version_code,
		app_version_name=app_version_name,
		min_sdk_version=min_sdk_version,
		target_sdk_version=target_sdk_version,
		package=package,
		icon=icon,
		icon_background=icon_background,
		icon_foreground=icon_foreground,
		presplash=presplash
	) # Gera o apk
	
	logger.success("Apk created")
	
	logger.info("Aligning apk")
			
	apkforge.APK.aligner(output_apk) # Alinha o apk em offsets divisivel de 4 bytes
	
	logger.success("Apk aligned")
	
	if apk_sign:
		logger.info("Signing apk")
		
		apkforge.APK.signer(output_apk, keystore_path, key_alias, keystore_pass=keystore_pass, key_pass=key_pass) # Assina o apk
		
		logger.success("Apk signed")
	else:
		logger.warning("Apk not signed")
	
	# Limpa o cache
	shutil.rmtree(cache_path)
	logger.success("Cache cleared")
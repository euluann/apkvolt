# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

from apkvolt import *
from . import zipalign
import argparse
import os
import logging
from .logger import logger, set_log_level
from .exceptions import APKVoltError
from getpass import getpass

def main():
	# Define configuração de logging
	logging.basicConfig(
		level=logging.INFO,
		format="[%(levelname)s] %(message)s"
	)
	parser = argparse.ArgumentParser(description="PVCompiler: Compile Python scripts into APKs")
	
	parser.add_argument(
		"--version",
		action="version",
		version="apkvolt 1.0.4"
	)
	
	# Cria subcomandos
	subparsers = parser.add_subparsers(dest="command", required=True)
	
	# Subcomando "compile"
	compile_parser = subparsers.add_parser("build", help="Build a project into APK")
	zipalign_parser = subparsers.add_parser("align", help="Align ZIP/APK entries.")
	
	# Subcomando "libs"
	libs_parser = subparsers.add_parser("libs", help="List supported libraries")
	
	# Adiciona os argumentos do zip de entrada e o zip de saida
	zipalign_parser.add_argument("input_zip")
	zipalign_parser.add_argument("output_zip")
	
	# Adiciona os argumentos opcionais para especificar os alinhamentos
	zipalign_parser.add_argument(
		"-a", "--alignment",
		type=int,
		default=4,
		help="Alignment for regular files (default: 4)."
	)
	zipalign_parser.add_argument(
		"-s", "--so-alignment",
		type=int,
		default=None,
		help="Alignment for .so files (default: same as alignment)."
	)
	
	# Argumento obrigatorio, indica onde esta o projeto a ser compilado
	compile_parser.add_argument("path", help="Path to your project")
	
	# Flags opcionais no comando do terminal
	compile_parser.add_argument("--sign", action="store_true", help="Sign the APK")
	compile_parser.add_argument("--ks", help="Keystore path")
	compile_parser.add_argument("--ks-alias", help="Key alias")
	compile_parser.add_argument("--app-name", help="App name")
	compile_parser.add_argument("--app-version-name", help="User-visible version string (e.g. 1.0.2)")
	compile_parser.add_argument("--app-version-code", type=int, help="Internal version integer used by Android for updates (must increase on each release)")
	compile_parser.add_argument("--min-sdk-version", type=int, help="Minimum android version the app is optimized for")
	compile_parser.add_argument("--target-sdk-version", type=int, help="Android version the app is optimized for")
	compile_parser.add_argument("--app-package", help="App package")
	compile_parser.add_argument("--output", help="Apk output name")
	compile_parser.add_argument("--icon", help="App compact icon path")
	compile_parser.add_argument("--icon-bg", help="App background icon path")
	compile_parser.add_argument("--icon-fg", help="App foreground icon path")
	compile_parser.add_argument("--splash", help="App loading screen icon path")
	compile_parser.add_argument("--log-level", help="APKVolt logs level (info, error, warning, debug)")
	
	
	args = parser.parse_args() # Faz o parsing automatico
	
	if args.command == "build":
		log_level = args.log_level
		if args.log_level is None:
			log_level = "info"
		try:
			set_log_level(log_level)
		except APKVoltError:
			raise SystemExit(1)
		if args.sign and (not args.ks or not args.ks_alias):
			logger.error("Signing requested without keystore or alias")
			raise SystemExit(1)
		
		if args.ks is not None:
			if not os.path.exists(args.ks):
				logger.error(f"Keystore not found: {args.ks}")
				raise SystemExit(1)
		if args.icon is not None:
			if not os.path.exists(args.icon):
				logger.error(f"Icon not found: {args.icon}")
				raise SystemExit(1)
		if args.icon_bg is not None:
			if not os.path.exists(args.icon_bg):
				logger.error(f"Background icon not found: {args.icon_bg}")
				raise SystemExit(1)
		if args.icon_fg is not None:
			if not os.path.exists(args.icon_fg):
				logger.error(f"Foreground icon not found: {args.icon_fg}")
				raise SystemExit(1)
		if args.splash is not None:
			if not os.path.exists(args.splash):
				logger.error(f"Splash image not found: {args.splash}")
				raise SystemExit(1)
		# Se foi solicitado assinamento, pede ao usuario a senha da keystore e da chave
		if args.sign:
			ks_pass = getpass("Keystore password: ")
			key_pass = getpass("Key password: ")
		else:
			ks_pass = None
			key_pass = None
		# Chama a funcao para compilar
		try:
			build(
				os.path.abspath(args.path),
				keystore_path=args.ks,
				key_alias=args.ks_alias,
				keystore_pass=ks_pass,
				key_pass=key_pass,
				apk_sign=args.sign,
				app_name=args.app_name,
				app_version_name=args.app_version_name,
				app_version_code=args.app_version_code,
				min_sdk_version=args.min_sdk_version,
				target_sdk_version=args.target_sdk_version,
				package=args.app_package,
				icon=args.icon,
				icon_background=args.icon_bg,
				icon_foreground=args.icon_fg,
				presplash=args.splash,
				output=args.output
			)
		except APKVoltError as e:
			logger.debug(e)
			raise SystemExit(1)
	elif args.command == "libs":
		print("Base libraries included in APK:")
		for lib in SUPPORTED_LIBS:
			print(f" - {lib}")
	elif args.command == "align":
		# Chama a funcao de alinhamento com as especificacoes fornecidas
		zipalign.align(
			args.input_zip,
			args.output_zip,
			alignment=args.alignment,
			so_alignment=args.so_alignment
		)
		print(f" ZIP/APK Aligned | {args.alignment} | so {args.so_alignment}")

if __name__ == "__main__":
	main()
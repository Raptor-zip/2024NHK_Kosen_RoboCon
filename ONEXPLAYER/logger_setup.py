import logging
from logging import Formatter, handlers
from logging import LogRecord, Logger, Formatter, StreamHandler, FileHandler, DEBUG, INFO
import os
import datetime
import WebServer

# ロガーを作成
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# def change_message(s: str) -> str:
#     if s == "\\\n":
#         return "\n\n\n\n\n"

#     s = s.upper().replace("\n", "\t")

#     if "CAT" in s:
#         s += "ฅ^•ω•^ฅﾆｬｰ"
#     return s

# class OriginalFormatter(Formatter):
#     def format(self, record: LogRecord) -> str:
#         # print("aaaaaaaaaaaaaaasaaaaaaaaaaaaaaaaaaaaaaaaa")
#         record.message = change_message(record.getMessage())
#         if self.usesTime():
#             record.asctime = self.formatTime(record, self.datefmt)
#         s = self.formatMessage(record)

#         if record.exc_info:
#             # Cache the traceback text to avoid converting it multiple times
#             # (it's constant anyway)
#             if not record.exc_text:
#                 record.exc_text = self.formatException(record.exc_info)
#         if record.exc_text:
#             if s[-1:] != "\n":
#                 s = s + "\n"
#             s = s + record.exc_text
#         if record.stack_info:
#             if s[-1:] != "\n":
#                 s = s + "\n"
#             s = s + self.formatStack(record.stack_info)
#         return ""



# ログレベルに対応した色付きマッピング（レベル名とメッセージの色両方）
level_color_mapping = {
    "TRACE": ("[ trace ]", "\x1b[37m"),  # 白
    "DEBUG": ("[ \x1b[0;36mdebug\x1b[0m ]", "\x1b[36m"),  # シアン
    "INFO": ("[  \x1b[0;32minfo\x1b[0m ]", "\x1b[32m"),  # 緑
    "WARNING": ("[  \x1b[0;33mwarn\x1b[0m ]", "\x1b[33m"),  # 黄
    "WARN": ("[  \x1b[0;33mwarn\x1b[0m ]", "\x1b[33m"),  # 黄
    "ERROR": ("\x1b[0;31m[ error ]\x1b[0m", "\x1b[31m"),  # 赤
    "ALERT": ("\x1b[0;37;41m[ alert ]\x1b[0m", "\x1b[31m"),  # 赤（背景付き）
    "CRITICAL": ("\x1b[0;37;41m[ alert ]\x1b[0m", "\x1b[31m"),  # 赤（背景付き）
}

# カスタムのカラフルなハンドラ
class ColorfulHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # 色付きのメッセージをコンソール用にだけ適用
        level_color, message_color = level_color_mapping.get(record.levelname, ("[ unknown ]", "\x1b[37m"))
        
        # レベル名を色付きに置き換え（コンソール出力のみに影響）
        colored_levelname = level_color
        colored_msg = f"{message_color}{record.msg}\x1b[0m"
        
        # 一時的にレコードを修正
        original_levelname = record.levelname
        original_msg = record.msg
        record.levelname = colored_levelname
        record.msg = colored_msg


        
        # ANSIエスケープシーケンス（色コード）を取り除いたメッセージを取得して表示
        formatted_log = self.format(record)
        # print(formatted_log)
        clean_message = self.remove_ansi_escape_sequences(formatted_log)
        # print(clean_message)
         # フォーマット済みのログメッセージを取得
        # コンソールにフォーマット済みのログメッセージを出力
        # WebServer.send_message_to_clients({"logger": clean_message})
        
        # 元のemitメソッドを呼び出す
        super().emit(record)
        
        # 修正を元に戻す
        record.levelname = original_levelname
        record.msg = original_msg

    def remove_ansi_escape_sequences(self, text: str) -> str:
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)

# log_format = OriginalFormatter("%(asctime)s %(name)s:%(lineno)s %(funcName)s [%(levelname)s]: %(message)s")

# st = StreamHandler()
# st.setFormatter(log_format)
# logger.addHandler(st)


# カスタムフォーマット（ファイル名、行番号、ミリ秒、レベル、メッセージ）
formatter:Formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] %(levelname)s: %(message)s', datefmt='%H:%M:%S')

# カラフルなハンドラを作成し、フォーマットを設定
color_handler = ColorfulHandler()
color_handler.setFormatter(formatter)

# ロガーにカラフルなハンドラを追加（標準出力）
logger.addHandler(color_handler)

# ファイルログ用のフォーマット（色を含まない）
file_formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] %(levelname)s: %(message)s', datefmt='%H:%M:%S')

# ログファイルの設定（回転ログ）
log_folder = "python_log"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

log_filename = os.path.join(log_folder, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
file_handler = handlers.RotatingFileHandler(log_filename, maxBytes=1000000, backupCount=10)

# ファイルハンドラには色を含まないフォーマットを設定
file_handler.setFormatter(file_formatter)

# ロガーにファイルハンドラを追加（ファイル出力用）
logger.addHandler(file_handler)
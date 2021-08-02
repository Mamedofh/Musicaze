# Daisyxmusic (Telegram bot project )
# Copyright (C) 2021  Inukaasith

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from DaisyXMusic.config import SOURCE_CODE,ASSISTANT_NAME,PROJECT_NAME,SUPPORT_GROUP,UPDATES_CHANNEL
class Messages():
      START_MSG = "**Hello 👋 [{}](tg://user?id={})!**\n\n🤖 I am an advanced bot created for playing music in the voice chats of Telegram Groups & Channels.\n\n✅ Send me /help for more info."
      HELP_MSG = [
        ".",
f"""
**Salam 👋 Yenidən Xoş Gəldin {PROJECT_NAME}

⚪️ {PROJECT_NAME} kanal və qrup səsli söhbətlərində musiqi oxuyur

⚪️ Assistan adı >> @{ASSISTANT_NAME}\n\nTəlimatlar üçün növbəti düyməni vurun**
""",

f"""
**Ayarlar**

1) Bot administratoru edin
2) Səsli söhbəti açın
3) yoxlayın /play [song name] ilk dəfə admin tərəfindən
*) Userbot qoşulsa musiqidən həzz alın, əlavə olunmasa @{ASSISTANT_NAME} qrupunuza manuel atın və yenidən cəhd edin

**Komandalar**

**=>> Mahnı oxuyur 🎧**

- /play: Youtube musiqisini istifadə edərək mahnını çalın
- /play [yt url] : Verilən yt link ilə oxudun
- /play [musiqiyə cavab verin]: Cavab verilən musiqini başladır

**=>> İzləmə ⏯**

- /player: Pleyerin Ayarlar menyusunu açın
- /skip: Mövcud parçanı atlayır
- /pause: İzləməyi dayandırın
- /resume: Dayandırılmış parçanı davam etdirir
- /end: Musiqinin oxunmasını dayandırır
- /current: Cari Çalma trekini göstərir
- /playlist: Musiqi Siyahısını göstərir
""",

f"""
**=>> Əlavələr 🧑‍🔧**

- /yenile: Qrupunuzun admin məlumatlarını yeniləyir. Bot admini tanımırsa cəhd edin
- /add: Asistanı @{ASSISTANT_NAME} qrupa dəvət edir

"""
      ]

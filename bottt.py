from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()


import discord
from discord.ext import commands
import asyncio
import json
import os
import time
import random
from datetime import datetime, timedelta, timezone
from collections import defaultdict

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================================================
# إعدادات عامة
# =========================================================

DATA_FILE = "levels_data.json"
TICKET_PANEL_IMAGE = "ticket_banner.png"  # حط الصورة بنفس مجلد البوت

# الكاتقريات
TICKET_CATEGORY_NAME = "TICKETS"
LOG_CATEGORY_NAME = "LOGS"
SYSTEM_CATEGORY_NAME = "BOT SYSTEM"

# رومات اللوق
TICKET_LOG_CHANNEL = "ticket-logs"
BAN_LOG_CHANNEL = "ban-logs"
KICK_LOG_CHANNEL = "kick-logs"
TIMEOUT_LOG_CHANNEL = "timeout-logs"
VOICE_LOG_CHANNEL = "voice-logs"
MUTE_LOG_CHANNEL = "mute-logs"
DEAFEN_LOG_CHANNEL = "deafen-logs"
MESSAGE_DELETE_LOG_CHANNEL = "message-delete-logs"
MESSAGE_EDIT_LOG_CHANNEL = "message-edit-logs"
SETUP_INFO_CHANNEL = "setup-info"
SECURITY_LOG_CHANNEL = "security-alerts"

# رومات النظام
LEVEL_ANNOUNCE_CHANNEL = "level-up"
TICKET_PANEL_CHANNEL = "ticket-panel"

# أسماء الرتب الإدارية بالترتيب المطلوب
OWNER_ROLE = "👑 Owner"
ABU_AWAD_ROLE = "أبو عواد"
ABU_FLAG_ROLE = "أبو فلاج"
CO_OWNER_ROLE = "🛡️ Co Owner"
FOUNDER_ROLE = "🔱 Founder"
HEAD_ADMIN_ROLE = "⚜️ Head Admin"
ADMIN_ROLE = "🛡️ Admin"

ADMIN_ROLE_ORDER = [
    OWNER_ROLE,
    ABU_AWAD_ROLE,
    ABU_FLAG_ROLE,
    CO_OWNER_ROLE,
    FOUNDER_ROLE,
    HEAD_ADMIN_ROLE,
    ADMIN_ROLE,
]

STAFF_ROLES = {
    OWNER_ROLE,
    CO_OWNER_ROLE,
    FOUNDER_ROLE,
    HEAD_ADMIN_ROLE,
    ADMIN_ROLE,
}

LOG_VIEW_ROLES = {
    OWNER_ROLE,
    CO_OWNER_ROLE,
    ABU_AWAD_ROLE,
    ABU_FLAG_ROLE,
}

ROLE_MANAGER_ROLES = {
    OWNER_ROLE,
    ABU_AWAD_ROLE,
    ABU_FLAG_ROLE,
}

OWNER_ONLY_ROLES = {
    OWNER_ROLE,
}

LEVEL_ROLE_CONFIG = [
    (1, "🌱 Newbie", 0x95A5A6),
    (5, "💬 Chatter", 0x3498DB),
    (10, "⭐ Active", 0xF1C40F),
    (15, "🔥 Regular", 0xE67E22),
    (25, "⚡ Veteran", 0x9B59B6),
    (35, "💎 Elite", 0x1ABC9C),
    (45, "👑 Legend", 0xE91E63),
]

LEVEL_ROLE_NAMES = [name for _, name, _ in LEVEL_ROLE_CONFIG]

# مضاعفات النظام
MESSAGE_XP_MIN = 8
MESSAGE_XP_MAX = 14
VOICE_XP_PER_MINUTE = 1
MESSAGE_COOLDOWN_SECONDS = 30

# الحماية
ANTINUKE_LIMIT = 30
ANTINUKE_WINDOW_SECONDS = 60

ticket_counter = 0

# بيانات الفلات
levels_data = {}
message_cooldowns = defaultdict(float)
voice_join_times = {}
mod_action_tracker = defaultdict(list)

# الأشياء اللي أنشأها البوت
BOT_CREATED_CHANNELS = {
    TICKET_LOG_CHANNEL,
    BAN_LOG_CHANNEL,
    KICK_LOG_CHANNEL,
    TIMEOUT_LOG_CHANNEL,
    VOICE_LOG_CHANNEL,
    MUTE_LOG_CHANNEL,
    DEAFEN_LOG_CHANNEL,
    MESSAGE_DELETE_LOG_CHANNEL,
    MESSAGE_EDIT_LOG_CHANNEL,
    SETUP_INFO_CHANNEL,
    SECURITY_LOG_CHANNEL,
    LEVEL_ANNOUNCE_CHANNEL,
    TICKET_PANEL_CHANNEL,
}
BOT_CREATED_CATEGORIES = {
    TICKET_CATEGORY_NAME,
    LOG_CATEGORY_NAME,
    SYSTEM_CATEGORY_NAME,
}
BOT_CREATED_ROLES = set(ADMIN_ROLE_ORDER) | set(LEVEL_ROLE_NAMES)

# =========================================================
# صلاحيات الرتب
# =========================================================

ROLE_PERMISSIONS = {
    OWNER_ROLE: discord.Permissions.all(),

    ABU_AWAD_ROLE: discord.Permissions(
        administrator=True
    ),

    ABU_FLAG_ROLE: discord.Permissions(
        administrator=True
    ),

    CO_OWNER_ROLE: discord.Permissions(
        administrator=True
    ),

    FOUNDER_ROLE: discord.Permissions(
        manage_guild=True,
        manage_roles=True,
        manage_channels=True,
        manage_messages=True,
        moderate_members=True,
        move_members=True,
        mute_members=True,
        deafen_members=True,
        view_audit_log=True,
        manage_nicknames=True,
        mention_everyone=True,
        read_messages=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
        speak=True,
        stream=True,
        use_voice_activation=True,
    ),

    HEAD_ADMIN_ROLE: discord.Permissions(
        manage_channels=True,
        manage_messages=True,
        moderate_members=True,
        move_members=True,
        mute_members=True,
        deafen_members=True,
        view_audit_log=True,
        manage_nicknames=True,
        read_messages=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
        speak=True,
        stream=True,
        use_voice_activation=True,
    ),

    ADMIN_ROLE: discord.Permissions(
        manage_messages=True,
        moderate_members=True,
        move_members=True,
        mute_members=True,
        deafen_members=True,
        manage_nicknames=True,
        read_messages=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
        speak=True,
        stream=True,
        use_voice_activation=True,
    ),
}

# =========================================================
# دوال حفظ وقراءة البيانات
# =========================================================

def load_levels():
    global levels_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                levels_data = json.load(f)
        except Exception:
            levels_data = {}
    else:
        levels_data = {}


def save_levels():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(levels_data, f, ensure_ascii=False, indent=2)


def guild_user_key(guild_id: int, user_id: int) -> str:
    return f"{guild_id}:{user_id}"


def get_user_data(guild_id: int, user_id: int):
    key = guild_user_key(guild_id, user_id)
    if key not in levels_data:
        levels_data[key] = {
            "xp": 0,
            "level": 0,
            "messages": 0,
            "voice_minutes": 0,
        }
    return levels_data[key]


def xp_for_level(level: int) -> int:
    return 100 + (level * 55)


def add_xp(guild_id: int, user_id: int, amount: int):
    user_data = get_user_data(guild_id, user_id)
    user_data["xp"] += amount

    leveled_up = False
    while user_data["xp"] >= xp_for_level(user_data["level"] + 1):
        user_data["level"] += 1
        leveled_up = True

    save_levels()
    return user_data["level"], leveled_up


# =========================================================
# دوال مساعدة
# =========================================================

def make_embed(title: str, description: str, color: discord.Color):
    return discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )


def get_channel_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.text_channels, name=name)


def get_category_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.categories, name=name)


def get_or_none_role(guild: discord.Guild, role_name: str):
    return discord.utils.get(guild.roles, name=role_name)


def has_any_role(member: discord.Member, role_names):
    return any(role.name in role_names for role in member.roles)


def is_owner_only_ctx(ctx):
    return has_any_role(ctx.author, OWNER_ONLY_ROLES)


def is_staff_ctx(ctx):
    return has_any_role(ctx.author, STAFF_ROLES)


def can_manage_role_names(ctx):
    return has_any_role(ctx.author, ROLE_MANAGER_ROLES)


def shorten_text(text: str, limit: int = 1000):
    if not text:
        return "ما فيه محتوى"
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


async def send_log(guild: discord.Guild, channel_name: str, embed: discord.Embed):
    channel = get_channel_by_name(guild, channel_name)
    if channel:
        await channel.send(embed=embed)


async def ensure_role(
    guild: discord.Guild,
    name: str,
    color_value: int = 0x2F3136,
    permissions: discord.Permissions | None = None,
    mentionable: bool = False
):
    """
    إذا الرتبة موجودة: يعدلها فقط
    إذا مو موجودة: ينشئها
    """
    role = get_or_none_role(guild, name)
    created = False

    if role is None:
        role = await guild.create_role(
            name=name,
            color=discord.Color(color_value),
            permissions=permissions or discord.Permissions.none(),
            mentionable=mentionable,
            reason="إنشاء رتبة بواسطة البوت"
        )
        created = True
    else:
        kwargs = {}
        if role.color.value != color_value:
            kwargs["color"] = discord.Color(color_value)

        if permissions is not None and role.permissions != permissions:
            kwargs["permissions"] = permissions

        if role.mentionable != mentionable:
            kwargs["mentionable"] = mentionable

        if kwargs:
            await role.edit(
                reason="تعديل إعدادات رتبة بواسطة البوت",
                **kwargs
            )

    return role, created


async def ensure_text_channel(guild: discord.Guild, category: discord.CategoryChannel, name: str, overwrites):
    channel = get_channel_by_name(guild, name)
    if channel is None:
        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            reason="إنشاء روم بواسطة البوت"
        )
    return channel


def build_log_overwrites(guild: discord.Guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            read_messages=False,
            send_messages=False
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True
        )
    }

    for role_name in LOG_VIEW_ROLES:
        role = get_or_none_role(guild, role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=False
            )

    return overwrites


def build_system_overwrites(guild: discord.Guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True,
            read_messages=True,
            send_messages=False
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True
        )
    }
    return overwrites


def build_ticket_category_overwrites(guild: discord.Guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            read_messages=False,
            send_messages=False
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            read_messages=True,
            send_messages=True
        )
    }

    for role_name in STAFF_ROLES | {ABU_AWAD_ROLE, ABU_FLAG_ROLE}:
        role = get_or_none_role(guild, role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=True
            )
    return overwrites


async def give_level_roles(member: discord.Member, new_level: int):
    guild = member.guild
    earned_role = None

    target_role = None
    for level_required, role_name, _ in LEVEL_ROLE_CONFIG:
        if new_level >= level_required:
            target_role = get_or_none_role(guild, role_name)

    if target_role:
        roles_to_remove = [r for r in member.roles if r.name in LEVEL_ROLE_NAMES and r != target_role]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="تحديث رتبة اللفل")

        if target_role not in member.roles:
            await member.add_roles(target_role, reason="ترقية لفل")
            earned_role = target_role

    return earned_role


async def announce_level_up(member: discord.Member, level: int, earned_role: discord.Role | None):
    channel = get_channel_by_name(member.guild, LEVEL_ANNOUNCE_CHANNEL)
    if not channel:
        return

    desc = f"{member.mention} وصل إلى **Level {level}** 🎉"
    if earned_role:
        desc += f"\nوأخذ رتبة {earned_role.mention}"

    embed = make_embed("📈 ترقية لفل", desc, discord.Color.green())
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(content=member.mention, embed=embed)


async def create_level_roles_if_missing(guild: discord.Guild):
    created = []
    for _, role_name, color_value in LEVEL_ROLE_CONFIG:
        _, was_created = await ensure_role(
            guild=guild,
            name=role_name,
            color_value=color_value,
            permissions=discord.Permissions.none(),
            mentionable=False
        )
        if was_created:
            created.append(role_name)
    return created


async def create_admin_roles_if_missing(guild: discord.Guild):
    created = []
    admin_colors = {
        OWNER_ROLE: 0xF1C40F,
        ABU_AWAD_ROLE: 0xE74C3C,
        ABU_FLAG_ROLE: 0x9B59B6,
        CO_OWNER_ROLE: 0x3498DB,
        FOUNDER_ROLE: 0x1ABC9C,
        HEAD_ADMIN_ROLE: 0xE67E22,
        ADMIN_ROLE: 0x95A5A6,
    }

    for role_name in ADMIN_ROLE_ORDER:
        _, was_created = await ensure_role(
            guild=guild,
            name=role_name,
            color_value=admin_colors.get(role_name, 0x2F3136),
            permissions=ROLE_PERMISSIONS.get(role_name, discord.Permissions.none()),
            mentionable=False
        )
        if was_created:
            created.append(role_name)

    return created


async def try_reorder_roles(guild: discord.Guild):
    if not guild.me.guild_permissions.manage_roles:
        return False

    position_base = max(2, guild.me.top_role.position - 1)
    roles_map = {}
    current_position = position_base

    # الإداري من فوق لتحت
    for role_name in ADMIN_ROLE_ORDER:
        role = get_or_none_role(guild, role_name)
        if role and role < guild.me.top_role:
            roles_map[role] = current_position
            current_position -= 1

    # الفلات من أعلى لفل إلى أقل لفل
    reversed_level_names = [name for _, name, _ in reversed(LEVEL_ROLE_CONFIG)]
    for role_name in reversed_level_names:
        role = get_or_none_role(guild, role_name)
        if role and role < guild.me.top_role:
            roles_map[role] = current_position
            current_position -= 1

    if roles_map:
        try:
            await guild.edit_role_positions(positions=roles_map)
            return True
        except discord.Forbidden:
            return False
        except Exception:
            return False
    return False


async def punish_suspicious_actor(guild: discord.Guild, actor: discord.Member, action_type: str, count: int):
    removable_roles = [
        role for role in actor.roles
        if role.name in STAFF_ROLES or role.name in {ABU_AWAD_ROLE, ABU_FLAG_ROLE, CO_OWNER_ROLE, FOUNDER_ROLE, HEAD_ADMIN_ROLE, ADMIN_ROLE}
    ]
    if removable_roles:
        try:
            await actor.remove_roles(*removable_roles, reason="Anti-nuke protection")
        except Exception:
            pass

    alert_channel = get_channel_by_name(guild, SECURITY_LOG_CHANNEL)
    owner_role = get_or_none_role(guild, OWNER_ROLE)

    embed = make_embed(
        "🚨 تنبيه حماية",
        f"تم رصد نشاط تخريبي محتمل.\n\n"
        f"**المنفذ:** {actor.mention}\n"
        f"**النوع:** {action_type}\n"
        f"**العدد خلال دقيقة:** {count}\n\n"
        f"تمت إزالة رتب الإدارة منه تلقائيًا.",
        discord.Color.red()
    )
    embed.set_thumbnail(url=actor.display_avatar.url)

    if alert_channel:
        content = owner_role.mention if owner_role else None
        await alert_channel.send(content=content, embed=embed)


async def register_mod_action(guild: discord.Guild, actor: discord.Member, action_type: str):
    key = (guild.id, actor.id, action_type)
    now = time.time()
    mod_action_tracker[key].append(now)
    mod_action_tracker[key] = [t for t in mod_action_tracker[key] if now - t <= ANTINUKE_WINDOW_SECONDS]

    count = len(mod_action_tracker[key])
    if count >= ANTINUKE_LIMIT:
        await punish_suspicious_actor(guild, actor, action_type, count)


# =========================================================
# setup
# =========================================================

@bot.command(aliases=["تهيئة", "setuplogs"])
@commands.check(is_owner_only_ctx)
async def setup(ctx):
    guild = ctx.guild

    created_roles = []
    created_roles += await create_admin_roles_if_missing(guild)
    created_roles += await create_level_roles_if_missing(guild)

    ticket_category = get_category_by_name(guild, TICKET_CATEGORY_NAME)
    if ticket_category is None:
        ticket_category = await guild.create_category(
            TICKET_CATEGORY_NAME,
            overwrites=build_ticket_category_overwrites(guild),
            reason="إنشاء كاتقري التيكت"
        )

    log_category = get_category_by_name(guild, LOG_CATEGORY_NAME)
    if log_category is None:
        log_category = await guild.create_category(
            LOG_CATEGORY_NAME,
            overwrites=build_log_overwrites(guild),
            reason="إنشاء كاتقري اللوق"
        )

    system_category = get_category_by_name(guild, SYSTEM_CATEGORY_NAME)
    if system_category is None:
        system_category = await guild.create_category(
            SYSTEM_CATEGORY_NAME,
            overwrites=build_system_overwrites(guild),
            reason="إنشاء كاتقري النظام"
        )

    created_channels = []

    log_overwrites = build_log_overwrites(guild)
    system_overwrites = build_system_overwrites(guild)

    log_channels = [
        TICKET_LOG_CHANNEL,
        BAN_LOG_CHANNEL,
        KICK_LOG_CHANNEL,
        TIMEOUT_LOG_CHANNEL,
        VOICE_LOG_CHANNEL,
        MUTE_LOG_CHANNEL,
        DEAFEN_LOG_CHANNEL,
        MESSAGE_DELETE_LOG_CHANNEL,
        MESSAGE_EDIT_LOG_CHANNEL,
        SETUP_INFO_CHANNEL,
        SECURITY_LOG_CHANNEL,
    ]

    for channel_name in log_channels:
        channel = get_channel_by_name(guild, channel_name)
        if channel is None:
            await guild.create_text_channel(
                channel_name,
                category=log_category,
                overwrites=log_overwrites,
                reason="إنشاء روم لوق"
            )
            created_channels.append(channel_name)

    system_channels = [
        LEVEL_ANNOUNCE_CHANNEL,
        TICKET_PANEL_CHANNEL,
    ]

    for channel_name in system_channels:
        channel = get_channel_by_name(guild, channel_name)
        if channel is None:
            await guild.create_text_channel(
                channel_name,
                category=system_category,
                overwrites=system_overwrites,
                reason="إنشاء روم نظام"
            )
            created_channels.append(channel_name)

    reordered = await try_reorder_roles(guild)

    embed = make_embed(
        "✅ تم تجهيز السيرفر",
        f"**تم إنشاء الرتب:**\n"
        f"{chr(10).join(f'• {r}' for r in created_roles) if created_roles else 'كل الرتب موجودة أصلًا أو تم تعديلها فقط.'}\n\n"
        f"**تم إنشاء الرومات:**\n"
        f"{chr(10).join(f'• {c}' for c in created_channels) if created_channels else 'كل الرومات موجودة أصلًا.'}\n\n"
        f"**ترتيب الرتب التلقائي:** {'نجح' if reordered else 'ما قدر البوت يرتبها، تأكد أن رتبته فوقها وعنده Manage Roles'}\n\n"
        f"**ملاحظة:** cleanup ما يحذف الرولات.",
        discord.Color.green()
    )
    await ctx.send(embed=embed)


# =========================================================
# أزرار التيكت
# =========================================================

class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 إقفال التيكت", style=discord.ButtonStyle.red, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_any_role(interaction.user, STAFF_ROLES | {ABU_AWAD_ROLE, ABU_FLAG_ROLE, OWNER_ROLE}):
            await interaction.response.send_message("ما عندك صلاحية تقفل التيكت.", ephemeral=True)
            return

        guild = interaction.guild
        channel = interaction.channel

        embed = make_embed(
            "🔒 تم إقفال التيكت",
            f"👮 **قفله:** {interaction.user.mention}\n📂 **الروم:** {channel.name}",
            discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await send_log(guild, TICKET_LOG_CHANNEL, embed)

        await interaction.response.send_message("بقفل التيكت بعد 3 ثواني...")
        await asyncio.sleep(3)
        await channel.delete(reason="تم إقفال التيكت")


async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    global ticket_counter
    guild = interaction.guild
    user = interaction.user

    for channel in guild.text_channels:
        if channel.name.startswith("ticket-") and channel.topic == f"ticket_owner:{user.id}":
            await interaction.response.send_message("عندك تيكت مفتوح من قبل.", ephemeral=True)
            return

    ticket_counter += 1

    category = get_category_by_name(guild, TICKET_CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(
            TICKET_CATEGORY_NAME,
            overwrites=build_ticket_category_overwrites(guild),
            reason="إنشاء كاتقري التيكت"
        )

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True),
    }

    for role_name in STAFF_ROLES | {ABU_AWAD_ROLE, ABU_FLAG_ROLE}:
        role = get_or_none_role(guild, role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=True
            )

    channel = await guild.create_text_channel(
        name=f"ticket-{ticket_counter}",
        overwrites=overwrites,
        category=category,
        topic=f"ticket_owner:{user.id}",
        reason="إنشاء تيكت"
    )

    staff_mentions = " ".join(
        role.mention for role in guild.roles
        if role.name in (STAFF_ROLES | {ABU_AWAD_ROLE, ABU_FLAG_ROLE})
    )

    embed = make_embed(
        "🎫 التيكت انفتح",
        f"هلا {user.mention}\n\n"
        f"**نوع الطلب:** {ticket_type}\n\n"
        f"اكتب التفاصيل هنا، والإدارة ترد عليك.",
        discord.Color.blurple()
    )
    embed.set_footer(text="Uncle Ticket System")

    await channel.send(content=staff_mentions if staff_mentions else None, embed=embed, view=TicketControls())

    log_embed = make_embed(
        "🎫 تيكت جديد",
        f"👤 **المستخدم:** {user.mention}\n"
        f"📂 **الروم:** {channel.mention}\n"
        f"📋 **النوع:** {ticket_type}",
        discord.Color.green()
    )
    log_embed.set_thumbnail(url=user.display_avatar.url)
    await send_log(guild, TICKET_LOG_CHANNEL, log_embed)

    await interaction.response.send_message(f"تم فتح التيكت: {channel.mention}", ephemeral=True)


class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎧 تواصل مع الإدارة", style=discord.ButtonStyle.primary, custom_id="panel_support")
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "تواصل مع الإدارة")

    @discord.ui.button(label="⚠️ شكوى إداري", style=discord.ButtonStyle.danger, custom_id="panel_admin_report")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "شكوى على إداري")

    @discord.ui.button(label="📩 شكوى على عضو", style=discord.ButtonStyle.secondary, custom_id="panel_member_report")
    async def member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "شكوى على عضو")

    @discord.ui.button(label="🛠️ مساعدة", style=discord.ButtonStyle.success, custom_id="panel_help")
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "طلب مساعدة")


@bot.command(aliases=["بانل", "tickets", "ticketpanel"])
@commands.check(is_owner_only_ctx)
async def panel(ctx):
    channel = get_channel_by_name(ctx.guild, TICKET_PANEL_CHANNEL)
    target = channel or ctx.channel

    embed = discord.Embed(
        title="🎟 Uncle Support Tickets",
        description=(
            "هلا والله 👋\n"
            "إذا عندك مشكلة أو شكوى أو استفسار افتح تيكت من الأزرار تحت.\n\n"
            "بينفتح لك روم خاص مع الإدارة."
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Uncle Server Support System")

    # إذا الصورة موجودة يرسلها كصورة مرفقة داخل الإمبد
    if os.path.exists(TICKET_PANEL_IMAGE):
        file = discord.File(TICKET_PANEL_IMAGE, filename="ticket_banner.png")
        embed.set_image(url="attachment://ticket_banner.png")
        await target.send(file=file, embed=embed, view=TicketPanel())
    else:
        await target.send(embed=embed, view=TicketPanel())

    if target != ctx.channel:
        await ctx.send(f"تم إرسال البانل في {target.mention} ✅")


# =========================================================
# help menu
# =========================================================

@bot.command(aliases=["helpstaff", "اوامر"])
async def helpmod(ctx):
    embed = make_embed(
        "📖 أوامر البوت",
        "**أوامر Owner فقط:**\n"
        "`!setup` / `!تهيئة`\n"
        "`!panel` / `!بانل`\n"
        "`!cleanup`\n\n"

        "**أوامر الإدارة:**\n"
        "`!mute @user السبب`\n"
        "`!unmute @user`\n"
        "`!deafen @user السبب`\n"
        "`!undeafen @user`\n"
        "`!timeout @user 10 السبب`\n"
        "`!untimeout @user`\n"
        "`!ban @user السبب`\n"
        "`!kick @user السبب`\n"
        "`!disconnect @user السبب`\n"
        "`!renamerole @Role الاسم الجديد`\n"
        "`!مسح 10` أو `!clear 10`\n\n"

        "**أوامر الفلات:**\n"
        "`!rank` أو `!rank @user`\n\n"

        "**لفلات التفاعل:**\n"
        "Level 1 — 🌱 Newbie\n"
        "Level 5 — 💬 Chatter\n"
        "Level 10 — ⭐ Active\n"
        "Level 15 — 🔥 Regular\n"
        "Level 25 — ⚡ Veteran\n"
        "Level 35 — 💎 Elite\n"
        "Level 45 — 👑 Legend",
        discord.Color.gold()
    )
    await ctx.send(embed=embed)


@bot.command(aliases=["sendcommands", "ارسلالشرح"])
@commands.check(is_owner_only_ctx)
async def sendhelp(ctx):
    channel = get_channel_by_name(ctx.guild, SETUP_INFO_CHANNEL)
    if channel is None:
        await ctx.send("روم setup-info مو موجود. شغّل `!setup` أول.")
        return

    embed = make_embed(
        "📖 شرح الأوامر",
        "تم إرسال قائمة الأوامر الأساسية.\n"
        "استخدم `!اوامر` لعرضها داخل أي روم.",
        discord.Color.blurple()
    )
    await channel.send(embed=embed)
    await ctx.send("تم إرسال الشرح في setup-info ✅")


# =========================================================
# أوامر الإدارة
# =========================================================

@bot.command(aliases=["اص", "m"])
@commands.check(is_staff_ctx)
async def mute(ctx, member: discord.Member, *, reason: str):
    if not member.voice:
        await ctx.send("العضو مو داخل فويس.")
        return

    await member.edit(mute=True, reason=reason)
    await ctx.send(f"🔇 تم ميوت {member.mention}")

    embed = make_embed(
        "🔇 ميوت",
        f"👤 **العضو:** {member.mention}\n"
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"📝 **السبب:** {reason}",
        discord.Color.orange()
    )
    await send_log(ctx.guild, MUTE_LOG_CHANNEL, embed)


@bot.command(aliases=["تكلم", "um"])
@commands.check(is_staff_ctx)
async def unmute(ctx, member: discord.Member):
    if not member.voice:
        await ctx.send("العضو مو داخل فويس.")
        return

    await member.edit(mute=False, reason=f"بواسطة {ctx.author}")
    await ctx.send(f"🔊 تم فك الميوت عن {member.mention}")

    embed = make_embed(
        "🔊 فك ميوت",
        f"👤 **العضو:** {member.mention}\n👮 **بواسطة:** {ctx.author.mention}",
        discord.Color.green()
    )
    await send_log(ctx.guild, MUTE_LOG_CHANNEL, embed)


@bot.command(aliases=["اسكت", "d"])
@commands.check(is_staff_ctx)
async def deafen(ctx, member: discord.Member, *, reason: str):
    if not member.voice:
        await ctx.send("العضو مو داخل فويس.")
        return

    await member.edit(deafen=True, reason=reason)
    await ctx.send(f"🎧 تم دفن {member.mention}")

    embed = make_embed(
        "🎧 دفن",
        f"👤 **العضو:** {member.mention}\n"
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"📝 **السبب:** {reason}",
        discord.Color.orange()
    )
    await send_log(ctx.guild, DEAFEN_LOG_CHANNEL, embed)


@bot.command(aliases=["اسمع", "ud"])
@commands.check(is_staff_ctx)
async def undeafen(ctx, member: discord.Member):
    if not member.voice:
        await ctx.send("العضو مو داخل فويس.")
        return

    await member.edit(deafen=False, reason=f"بواسطة {ctx.author}")
    await ctx.send(f"🔉 تم فك الدفن عن {member.mention}")

    embed = make_embed(
        "🔉 فك دفن",
        f"👤 **العضو:** {member.mention}\n👮 **بواسطة:** {ctx.author.mention}",
        discord.Color.green()
    )
    await send_log(ctx.guild, DEAFEN_LOG_CHANNEL, embed)


@bot.command(aliases=["وقت", "to"])
@commands.check(is_staff_ctx)
async def timeout(ctx, member: discord.Member, minutes: int, *, reason: str):
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await ctx.send(f"⏳ تم إعطاء تايم أوت لـ {member.mention} لمدة {minutes} دقيقة")

    embed = make_embed(
        "⏳ تايم أوت",
        f"👤 **العضو:** {member.mention}\n"
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"⏱️ **المدة:** {minutes} دقيقة\n"
        f"📝 **السبب:** {reason}",
        discord.Color.orange()
    )
    await send_log(ctx.guild, TIMEOUT_LOG_CHANNEL, embed)


@bot.command(aliases=["فكوقت", "uto"])
@commands.check(is_staff_ctx)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=f"بواسطة {ctx.author}")
    await ctx.send(f"✅ تم فك التايم أوت عن {member.mention}")

    embed = make_embed(
        "✅ فك التايم أوت",
        f"👤 **العضو:** {member.mention}\n👮 **بواسطة:** {ctx.author.mention}",
        discord.Color.green()
    )
    await send_log(ctx.guild, TIMEOUT_LOG_CHANNEL, embed)


@bot.command(aliases=["انقلع", "b"])
@commands.check(is_staff_ctx)
async def ban(ctx, member: discord.Member, *, reason: str):
    await member.ban(reason=reason)
    await ctx.send(f"🚫 تم تبنيد {member.mention}")

    embed = make_embed(
        "🚫 بان",
        f"👤 **العضو:** {member.mention}\n"
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"📝 **السبب:** {reason}",
        discord.Color.red()
    )
    await send_log(ctx.guild, BAN_LOG_CHANNEL, embed)
    await register_mod_action(ctx.guild, ctx.author, "ban")


@bot.command(aliases=["برا", "k"])
@commands.check(is_staff_ctx)
async def kick(ctx, member: discord.Member, *, reason: str):
    await member.kick(reason=reason)
    await ctx.send(f"👢 تم طرد {member.mention}")

    embed = make_embed(
        "👢 كيك",
        f"👤 **العضو:** {member.mention}\n"
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"📝 **السبب:** {reason}",
        discord.Color.red()
    )
    await send_log(ctx.guild, KICK_LOG_CHANNEL, embed)
    await register_mod_action(ctx.guild, ctx.author, "kick")


@bot.command(aliases=["اطلع", "dc"])
@commands.check(is_staff_ctx)
async def disconnect(ctx, member: discord.Member, *, reason: str):
    if not member.voice or not member.voice.channel:
        await ctx.send("العضو مو داخل فويس.")
        return

    old_channel = member.voice.channel
    await member.move_to(None, reason=reason)
    await ctx.send(f"📴 تم فصل {member.mention} من الفويس")

    embed = make_embed(
        "📴 فصل من الفويس",
        f"👤 **العضو:** {member.mention}\n"
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"🔊 **من روم:** {old_channel.mention}\n"
        f"📝 **السبب:** {reason}",
        discord.Color.red()
    )
    await send_log(ctx.guild, VOICE_LOG_CHANNEL, embed)


@bot.command(aliases=["rr", "roleedit", "تعديلرتبة"])
@commands.check(can_manage_role_names)
async def renamerole(ctx, role: discord.Role, *, new_name: str):
    if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        await ctx.send("ما تقدر تعدل رتبة أعلى منك أو نفس مستواك.")
        return

    if role >= ctx.guild.me.top_role:
        await ctx.send("الرتبة أعلى من البوت. ارفع رتبة البوت فوقها.")
        return

    old_name = role.name
    await role.edit(name=new_name, reason=f"بواسطة {ctx.author}")

    await ctx.send(f"✅ تم تغيير اسم الرتبة من **{old_name}** إلى **{new_name}**")

    embed = make_embed(
        "🏷️ تعديل اسم رتبة",
        f"👮 **بواسطة:** {ctx.author.mention}\n"
        f"📌 **الاسم القديم:** {old_name}\n"
        f"✨ **الاسم الجديد:** {new_name}",
        discord.Color.gold()
    )
    await send_log(ctx.guild, SETUP_INFO_CHANNEL, embed)


@bot.command(aliases=["clear", "purge"])
@commands.check(is_staff_ctx)
@commands.has_permissions(manage_messages=True)
async def مسح(ctx, amount: int):
    if amount < 1:
        await ctx.send("اكتب رقم أكبر من 0.")
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 تم مسح **{len(deleted) - 1}** رسالة.")
    await asyncio.sleep(3)
    await msg.delete()


@bot.command()
@commands.check(is_owner_only_ctx)
async def cleanup(ctx):
    guild = ctx.guild
    deleted_channels = []
    deleted_categories = []

    # حذف رومات التيكت المفتوحة
    for channel in list(guild.text_channels):
        if channel.name.startswith("ticket-"):
            try:
                await channel.delete(reason="Owner cleanup")
                deleted_channels.append(channel.name)
            except Exception:
                pass

    # حذف الرومات الثابتة
    for channel in list(guild.text_channels):
        if channel.name in BOT_CREATED_CHANNELS:
            try:
                await channel.delete(reason="Owner cleanup")
                deleted_channels.append(channel.name)
            except Exception:
                pass

    # حذف الكاتقريات
    for category in list(guild.categories):
        if category.name in BOT_CREATED_CATEGORIES:
            try:
                await category.delete(reason="Owner cleanup")
                deleted_categories.append(category.name)
            except Exception:
                pass

    # مهم: لا يحذف الرولات
    embed = make_embed(
        "🗑️ تم التنظيف",
        f"**الرومات المحذوفة:**\n"
        f"{chr(10).join(f'• {x}' for x in deleted_channels) if deleted_channels else 'ما فيه'}\n\n"
        f"**الكاتقريات المحذوفة:**\n"
        f"{chr(10).join(f'• {x}' for x in deleted_categories) if deleted_categories else 'ما فيه'}\n\n"
        f"**الرولات:** لم يتم حذف أي رتبة ✅",
        discord.Color.red()
    )
    await ctx.send(embed=embed)


# =========================================================
# أوامر الفلات
# =========================================================

@bot.command(aliases=["lv", "level", "رانك"])
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = get_user_data(ctx.guild.id, member.id)

    current_level = data["level"]
    current_xp = data["xp"]
    next_level_xp = xp_for_level(current_level + 1)

    embed = make_embed(
        "📊 Rank",
        f"👤 **العضو:** {member.mention}\n"
        f"⭐ **Level:** {current_level}\n"
        f"✨ **XP:** {current_xp}/{next_level_xp}\n"
        f"💬 **الرسائل:** {data['messages']}\n"
        f"🎧 **دقائق الفويس:** {data['voice_minutes']}",
        discord.Color.blurple()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)


# =========================================================
# لوقات الرسائل
# =========================================================

@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    embed = make_embed(
        "🗑️ رسالة محذوفة",
        f"👤 **العضو:** {message.author.mention}\n"
        f"📂 **الروم:** {message.channel.mention}\n\n"
        f"**محتوى الرسالة:**\n{shorten_text(message.content, 1500)}",
        discord.Color.red()
    )
    embed.set_thumbnail(url=message.author.display_avatar.url)
    await send_log(message.guild, MESSAGE_DELETE_LOG_CHANNEL, embed)


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or not before.guild:
        return
    if before.content == after.content:
        return

    embed = make_embed(
        "✏️ رسالة معدلة",
        f"👤 **العضو:** {before.author.mention}\n"
        f"📂 **الروم:** {before.channel.mention}\n\n"
        f"**قبل:**\n{shorten_text(before.content, 800)}\n\n"
        f"**بعد:**\n{shorten_text(after.content, 800)}",
        discord.Color.orange()
    )
    embed.set_thumbnail(url=before.author.display_avatar.url)
    await send_log(before.guild, MESSAGE_EDIT_LOG_CHANNEL, embed)


# =========================================================
# لوقات الفويس + نظام الفلات
# =========================================================

@bot.event
async def on_voice_state_update(member, before, after):
    log = get_channel_by_name(member.guild, VOICE_LOG_CHANNEL)

    if before.channel is None and after.channel is not None:
        voice_join_times[(member.guild.id, member.id)] = time.time()
        if log:
            embed = make_embed(
                "🎧 دخول فويس",
                f"👤 **العضو:** {member.mention}\n🔊 **الروم:** {after.channel.mention}",
                discord.Color.blue()
            )
            await log.send(embed=embed)

    elif before.channel is not None and after.channel is None:
        join_key = (member.guild.id, member.id)
        joined_at = voice_join_times.pop(join_key, None)
        if joined_at:
            minutes = int((time.time() - joined_at) / 60)
            if minutes > 0:
                data = get_user_data(member.guild.id, member.id)
                data["voice_minutes"] += minutes
                level, leveled_up = add_xp(member.guild.id, member.id, minutes * VOICE_XP_PER_MINUTE)
                if leveled_up:
                    earned_role = await give_level_roles(member, level)
                    await announce_level_up(member, level, earned_role)

        if log:
            embed = make_embed(
                "📴 خروج من الفويس",
                f"👤 **العضو:** {member.mention}\n🔊 **كان في:** {before.channel.name}",
                discord.Color.red()
            )
            await log.send(embed=embed)

    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        if log:
            embed = make_embed(
                "🔁 انتقال فويس",
                f"👤 **العضو:** {member.mention}\n"
                f"📤 **من:** {before.channel.mention}\n"
                f"📥 **إلى:** {after.channel.mention}",
                discord.Color.blurple()
            )
            await log.send(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild:
        now = time.time()
        cooldown_key = (message.guild.id, message.author.id)
        last_time = message_cooldowns[cooldown_key]

        if now - last_time >= MESSAGE_COOLDOWN_SECONDS:
            message_cooldowns[cooldown_key] = now
            data = get_user_data(message.guild.id, message.author.id)
            data["messages"] += 1

            gained_xp = random.randint(MESSAGE_XP_MIN, MESSAGE_XP_MAX)
            level, leveled_up = add_xp(message.guild.id, message.author.id, gained_xp)

            if leveled_up:
                earned_role = await give_level_roles(message.author, level)
                await announce_level_up(message.author, level, earned_role)

    await bot.process_commands(message)


# =========================================================
# حماية البان/الكيك
# =========================================================

@bot.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
    try:
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id and (discord.utils.utcnow() - entry.created_at).total_seconds() <= 10:
                actor = entry.user
                if isinstance(actor, discord.Member):
                    await register_mod_action(guild, actor, "ban")
                break
    except Exception:
        pass


@bot.event
async def on_member_remove(member: discord.Member):
    try:
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() <= 10:
                actor = entry.user
                if isinstance(actor, discord.Member):
                    await register_mod_action(member.guild, actor, "kick")
                break
    except Exception:
        pass


# =========================================================
# أخطاء الأوامر
# =========================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("ما عندك صلاحية تستخدم هالأمر.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("ناقصك براميتر في الأمر.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("ما لقيت العضو.")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("ما لقيت الرتبة.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("فيه خطأ بالمدخلات.")
    else:
        raise error


# =========================================================
# تشغيل البوت
# =========================================================

@bot.event
async def on_ready():
    load_levels()
    bot.add_view(TicketPanel())
    bot.add_view(TicketControls())
    print(f"البوت اشتغل: {bot.user}")


keep_alive()
TOKEN = ""
bot.run("")

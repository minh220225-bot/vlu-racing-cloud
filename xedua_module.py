# -*- coding: utf-8 -*-
import os, json, time
from flask import Blueprint, request, jsonify, Response, send_file

xedua_bp = Blueprint('xedua', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LED_CONFIG_FILE = os.path.join(BASE_DIR, "led_config_racing.json")

DEFAULT_LED_CONFIG = {
    "left_color": "#FFAA00", "right_color": "#FFAA00", "drl_color": "#00E5FF",
    "sync_sides": True, "mode": "audi", "brightness": 90, "speed_ms": 280,
    "drl_enabled": True, "turn_always_fx": False, "swap_turn_dir": False,
    "ug_color1": "#00E5FF", "ug_color2": "#9D00FF", "ug_mode": "neon_cyber",
    "ug_speed_ms": 240, "ug_brightness": 85, "ug_enabled": True, "ug_rev_left": False,
    "intro_mode": "audi_rs", "intro_enabled": True
}

cfg_version = 1

def load_led_config():
    if os.path.exists(LED_CONFIG_FILE):
        try:
            with open(LED_CONFIG_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                res = dict(DEFAULT_LED_CONFIG)
                res.update(d)
                return res
        except Exception:
            pass
    return dict(DEFAULT_LED_CONFIG)

def save_led_config(cfg):
    global cfg_version
    try:
        with open(LED_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        cfg_version += 1
        return True
    except Exception:
        return False

led_config = load_led_config()

car_state = {
    "online": False, "last_seen": 0.0, "ip": "Cloud-Connected",
    "pitch": 0.0, "roll": 0.0, "yaw": 0.0, "g": 1.00,
    "air": 0, "corr": 0, "thr": 0, "str": 0, "esc": 1500, "srv": 90,
    "bat": 7.8, "link": 0, "spd": 0.0, "maxSpd": 0.0, "jmpSpd": 0.0,
    "cap": 100, "ota_msg": "Render Cloud s?n s?ng ??ng b? v?i Xe"
}

pending_commands = {
    "test_action": None, "test_in_mode": None, "zero_imu": False,
    "tune_qs": None, "ota_url": None
}

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VLU RACING CENTER - IMU & RGB LED STUDIO</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #06090f;
      color: #e6edf3;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 16px;
    }
    .container {
      max-width: 1140px;
      margin: 0 auto;
    }
    header {
      background: linear-gradient(135deg, #1b0c2e 0%, #0d1b2a 100%);
      border: 1px solid #ff6a0088;
      border-radius: 14px;
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 12px;
      box-shadow: 0 0 25px rgba(255, 106, 0, 0.18);
    }
    .title-area h1 { font-size: 1.25rem; color: #ff7b00; letter-spacing: 1px; }
    .title-area p  { font-size: 0.78rem; color: #8b949e; margin-top: 3px; }
    .status-pills  { display: flex; gap: 8px; flex-wrap: wrap; }
    .pill {
      padding: 6px 14px; border-radius: 20px; font-size: 0.76rem; font-weight: 700;
      background: #161b22; border: 1px solid #30363d; color: #8b949e;
    }
    .pill.online  { background: #0d3822; color: #3fb950; border-color: #238636; }
    .pill.offline { background: #3d1418; color: #ff7b72; border-color: #da3633; }
    .pill.air     { background: #4d2200; color: #ff9900; border-color: #ff6600; animation: blink 0.5s infinite; }
    @keyframes blink { 50% { opacity: 0.4; } }

    /* NAVIGATION TABS */
    .nav-bar {
      display: flex; gap: 10px; margin-bottom: 16px; background: #0c111c;
      padding: 6px; border-radius: 12px; border: 1px solid #242f42;
    }
    .nav-btn {
      flex: 1; padding: 12px 18px; border: none; border-radius: 8px;
      font-size: 0.88rem; font-weight: 800; cursor: pointer; color: #8b949e;
      background: transparent; transition: all 0.2s ease;
      display: flex; align-items: center; justify-content: center; gap: 8px;
    }
    .nav-btn:hover { color: #fff; background: #162033; }
    .nav-btn.active {
      color: #fff; background: linear-gradient(135deg, #ff7b00 0%, #ff3b30 100%);
      box-shadow: 0 0 18px rgba(255, 123, 0, 0.45);
    }
    .nav-btn.led-tab.active {
      background: linear-gradient(135deg, #8957e5 0%, #00e5ff 100%);
      box-shadow: 0 0 18px rgba(0, 229, 255, 0.45);
    }

    .tab-content { display: none; }
    .tab-content.active { display: block; }

    .main-grid {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 16px;
    }
    @media (max-width: 860px) {
      .main-grid { grid-template-columns: 1fr; }
    }
    .panel {
      background: #0f141f;
      border: 1px solid #242f42;
      border-radius: 14px;
      padding: 16px;
    }
    .ptitle {
      font-size: 0.82rem; font-weight: 800; color: #ff7b00;
      text-transform: uppercase; letter-spacing: 0.8px;
      margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;
    }
    .hud-box {
      display: flex; flex-direction: column; align-items: center; gap: 12px;
    }
    .hud-circle {
      width: 320px; height: 320px; border-radius: 50%;
      border: 3px solid #ff7b00; overflow: hidden;
      box-shadow: 0 0 30px rgba(255,123,0,0.28), inset 0 0 18px #000;
    }
    canvas { width: 100%; height: 100%; display: block; }
    .corr-status {
      width: 100%; background: #161b22; border: 1px solid #30363d;
      border-radius: 10px; padding: 10px; text-align: center; font-size: 0.85rem; font-weight: 700;
    }
    .right-col { display: flex; flex-direction: column; gap: 16px; }
    .cards {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
    }
    .card {
      background: #141b29; border: 1px solid #26334d; border-radius: 10px;
      padding: 10px; text-align: center;
    }
    .card .lbl { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; }
    .card .val { font-size: 1.45rem; font-weight: 800; margin-top: 4px; font-variant-numeric: tabular-nums; }
    .card .sub { font-size: 0.68rem; color: #6e7681; margin-top: 3px; }

    .btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
    .btn {
      flex: 1; min-width: 170px; padding: 12px 14px; border-radius: 9px; border: none;
      font-size: 0.82rem; font-weight: 700; cursor: pointer; color: #fff;
      transition: transform 0.1s, opacity 0.2s;
    }
    .btn:active { transform: scale(0.98); }
    .btn-purple { background: #8957e5; }
    .btn-green  { background: #238636; }
    .btn-blue   { background: #1f6feb; }
    .btn-orange { background: #d29922; color: #000; }
    .btn-cyan   { background: #00b4d8; color: #000; }
    .btn-dark   { background: #21262d; border: 1px solid #30363d; }

    .srow { display: flex; align-items: center; gap: 10px; margin-bottom: 9px; font-size: 0.8rem; }
    .srow label { width: 190px; color: #c9d1d9; }
    .srow input[type=range] { flex: 1; accent-color: #ff7b00; }
    .srow span { width: 55px; text-align: right; color: #ff7b00; font-weight: 700; }

    .ota-log {
      margin-top: 10px; background: #090d14; border: 1px solid #21262d;
      border-radius: 8px; padding: 10px; font-family: monospace; font-size: 0.78rem;
      color: #58a6ff;
    }

    /* =========================================================================
       CSS RIÊNG BIỆT CHO STUDIO DÀN ĐÈN 6 CỤM (32 LED WS2812B: 4 XI NHAN + 2 GẦM)
       ========================================================================= */
    .led-grid {
      display: grid; grid-template-columns: 420px 1fr; gap: 16px; align-items: start;
    }
    @media (max-width: 920px) {
      .led-grid { grid-template-columns: 1fr; }
    }

    /* Khung mô phỏng xe 2D 32 Bóng LED thực tế */
    .car-sim-card {
      background: radial-gradient(circle at center, #101b30 0%, #060a12 100%);
      border: 1px solid #00e5ff66; border-radius: 16px; padding: 16px;
      display: flex; flex-direction: column; align-items: center; gap: 12px;
      box-shadow: 0 0 28px rgba(0, 229, 255, 0.14);
      position: sticky; top: 14px;
    }
    .car-chassis-box {
      width: 310px; height: 450px; position: relative; margin: 4px 0;
      display: flex; align-items: center; justify-content: center;
      background: radial-gradient(ellipse at center, rgba(0,229,255,0.06) 0%, transparent 72%);
      border-radius: 20px;
    }
    .car-svg {
      width: 220px; height: 390px; filter: drop-shadow(0 0 18px rgba(0,0,0,0.95)); z-index: 3;
    }
    .led-underglow-fx {
      position: absolute; top: 95px; left: 55px; width: 200px; height: 260px;
      border-radius: 50px; opacity: 0.42; filter: blur(34px); pointer-events: none; z-index: 1;
      transition: background 0.15s, opacity 0.15s;
    }

    /* 4 Cụm Xi Nhan (Mỗi cụm 2 LED = 8 LED: 0..7) */
    .turn-cluster {
      position: absolute; display: flex; gap: 5px; padding: 4px 6px;
      background: rgba(8, 13, 24, 0.9); border: 1.5px solid #304260;
      border-radius: 12px; z-index: 12; align-items: center;
      box-shadow: 0 2px 10px rgba(0,0,0,0.8);
    }
    .turn-cluster.c1-fr { top: 28px; right: 44px; }   /* Cụm 1: Phải Trước (LED 0, 1) */
    .turn-cluster.c2-fl { top: 28px; left: 44px; }    /* Cụm 2: Trái Trước (LED 2, 3) */
    .turn-cluster.c3-rl { bottom: 26px; left: 44px; } /* Cụm 3: Trái Đuôi  (LED 4, 5) */
    .turn-cluster.c4-rr { bottom: 26px; right: 44px; }/* Cụm 4: Phải Đuôi  (LED 6, 7) */

    .led-pixel-turn {
      width: 15px; height: 15px; border-radius: 50%;
      background: #182030; border: 1.5px solid #445878;
      transition: background 0.06s, box-shadow 0.06s, transform 0.06s;
      position: relative;
    }

    /* 2 Cụm Đèn Gầm (Mỗi cụm 12 LED = 24 LED: 8..19 & 20..31) */
    .ug-strip {
      position: absolute; top: 82px; height: 286px; width: 22px;
      display: flex; flex-direction: column; justify-content: space-between;
      align-items: center; padding: 6px 3px;
      background: rgba(8, 12, 22, 0.88); border: 1.5px solid #2b3c58;
      border-radius: 12px; z-index: 11;
    }
    .ug-strip.c5-right { right: 16px; } /* Cụm 5: Gầm Phải (LED 8..19) */
    .ug-strip.c6-left  { left: 16px; }  /* Cụm 6: Gầm Trái (LED 20..31) */

    .led-pixel-ug {
      width: 13px; height: 16px; border-radius: 4px;
      background: #161e2e; border: 1px solid #384c6d;
      transition: background 0.05s, box-shadow 0.05s;
    }

    /* Nhãn thứ tự cụm dây nối (Hiện/Ẩn) */
    .cluster-badge {
      position: absolute; font-size: 0.63rem; font-weight: 900;
      padding: 2px 6px; border-radius: 6px; background: #071324ee;
      border: 1px solid #00e5ffaa; color: #00e5ff; z-index: 20;
      white-space: nowrap; pointer-events: none;
      box-shadow: 0 0 8px rgba(0,229,255,0.35);
    }
    .cluster-badge.b1 { top: 6px; right: 24px; }
    .cluster-badge.b2 { top: 6px; left: 24px; }
    .cluster-badge.b3 { bottom: 4px; left: 20px; }
    .cluster-badge.b4 { bottom: 4px; right: 20px; }
    .cluster-badge.b5 { top: 58px; right: 4px; color: #ff9900; border-color: #ff9900aa; }
    .cluster-badge.b6 { top: 58px; left: 4px; color: #d2a8ff; border-color: #d2a8ffaa; }

    .wiring-summary {
      width: 100%; background: #09111e; border: 1px solid #1f324d;
      border-radius: 10px; padding: 9px 11px; font-size: 0.72rem; line-height: 1.5;
      color: #9ecbff;
    }
    .wiring-summary b { color: #00e5ff; }

    .test-actions-box {
      width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-top: 2px;
    }
    .test-actions-box button {
      padding: 9px 8px; border-radius: 8px; font-size: 0.75rem; font-weight: 800;
      border: 1px solid #26334d; background: #141b29; color: #fff; cursor: pointer;
      transition: all 0.15s ease;
    }
    .test-actions-box button:hover { background: #1c273a; border-color: #00e5ff; }
    .test-actions-box button.active {
      background: #00e5ff22; border-color: #00e5ff; color: #00e5ff;
      box-shadow: 0 0 12px rgba(0, 229, 255, 0.3);
    }

    /* BẢNG VÒNG TRÒN MÀU 360° & DẢI QUANG PHỔ CẦU VỒNG 2D (NHƯ HÌNH GỬI) */
    .color-studio-wrap {
      display: grid; grid-template-columns: 195px 1fr; gap: 14px; align-items: center;
      background: #090e18; border: 1px solid #253551; border-radius: 14px; padding: 14px;
      margin-bottom: 12px;
    }
    @media (max-width: 680px) {
      .color-studio-wrap { grid-template-columns: 1fr; justify-items: center; }
    }
    .wheel-box {
      position: relative; width: 184px; height: 184px;
      display: flex; align-items: center; justify-content: center;
    }
    #colorWheelCanvas {
      width: 184px; height: 184px; border-radius: 50%; cursor: crosshair;
      box-shadow: 0 0 20px rgba(0, 229, 255, 0.22), inset 0 0 8px rgba(0,0,0,0.6);
      border: 2px solid #354b6e;
    }
    .wheel-cursor {
      position: absolute; width: 18px; height: 18px; border-radius: 50%;
      border: 3px solid #fff; box-shadow: 0 0 8px #000, inset 0 0 4px #000;
      pointer-events: none; transform: translate(-50%, -50%);
      top: 50%; left: 50%; z-index: 5;
    }

    .spectrum-box-wrap {
      width: 100%; display: flex; flex-direction: column; gap: 8px;
    }
    .spectrum-canvas-holder {
      position: relative; width: 100%; height: 132px; border-radius: 12px;
      overflow: hidden; border: 2px solid #3a5078;
      box-shadow: 0 0 18px rgba(188, 140, 255, 0.18);
    }
    #rainbowSpectrumCanvas {
      width: 100%; height: 100%; display: block; cursor: crosshair;
    }
    .spectrum-cursor {
      position: absolute; width: 18px; height: 18px; border-radius: 50%;
      border: 3px solid #fff; box-shadow: 0 0 8px #000, inset 0 0 4px #000;
      pointer-events: none; transform: translate(-50%, -50%);
      top: 30%; left: 10%; z-index: 5;
    }

    /* Nút chọn vùng đèn đang chỉnh màu (5 vùng) */
    .target-tabs {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
      gap: 7px; margin-bottom: 12px;
    }
    .target-pill {
      display: flex; align-items: center; gap: 8px; padding: 9px 10px;
      border-radius: 10px; background: #121a2a; border: 1.5px solid #263652;
      cursor: pointer; transition: all 0.16s ease; color: #c9d1d9;
    }
    .target-pill:hover { border-color: #58a6ff; background: #172338; }
    .target-pill.active {
      border-color: #00e5ff; background: #0d273d;
      box-shadow: 0 0 14px rgba(0, 229, 255, 0.32); color: #fff;
    }
    .target-dot {
      width: 20px; height: 20px; border-radius: 6px; border: 2px solid #fff;
      flex-shrink: 0; box-shadow: 0 0 8px currentColor;
    }
    .target-txt { display: flex; flex-direction: column; text-align: left; }
    .target-txt b { font-size: 0.74rem; line-height: 1.15; }
    .target-txt span { font-size: 0.64rem; color: #8b949e; }

    /* Ô màu mẫu Swatches */
    .swatches-bar {
      display: grid; grid-template-columns: repeat(6, 1fr); gap: 7px; margin-top: 8px;
    }
    @media (max-width: 680px) {
      .swatches-bar { grid-template-columns: repeat(3, 1fr); }
    }
    .swatch-pill {
      display: flex; align-items: center; gap: 6px; padding: 7px 8px; border-radius: 8px;
      background: #141b29; border: 1px solid #26334d; color: #c9d1d9;
      font-size: 0.7rem; font-weight: 700; cursor: pointer; transition: all 0.15s ease;
    }
    .swatch-pill:hover { border-color: #00e5ff; transform: translateY(-2px); }
    .swatch-color {
      width: 13px; height: 13px; border-radius: 50%; flex-shrink: 0;
    }

    /* Card chế độ hiệu ứng */
    .mode-card-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(128px, 1fr)); gap: 8px; margin-top: 8px;
    }
    .mode-card {
      background: #131b2b; border: 1.5px solid #25344f; border-radius: 10px;
      padding: 10px 8px; text-align: center; cursor: pointer; transition: all 0.18s ease;
    }
    .mode-card:hover { border-color: #58a6ff; background: #18243a; transform: translateY(-1px); }
    .mode-card.active {
      border-color: #00e5ff; background: #0c273b; box-shadow: 0 0 15px rgba(0, 229, 255, 0.32);
    }
    .mode-card.ug-card.active {
      border-color: #d2a8ff; background: #22143b; box-shadow: 0 0 15px rgba(210, 168, 255, 0.35);
    }
    .mode-card.intro-card.active {
      border-color: #3fb950; background: #0d2b1a; box-shadow: 0 0 15px rgba(63, 185, 80, 0.38);
    }
    .mode-card .m-icon { font-size: 1.35rem; margin-bottom: 3px; }
    .mode-card .m-name { font-size: 0.75rem; font-weight: 800; color: #fff; }
    .mode-card .m-desc { font-size: 0.63rem; color: #8b949e; margin-top: 2px; line-height: 1.2; }

    .sync-toggle-box {
      display: flex; align-items: center; justify-content: space-between;
      background: #0d1e2e; border: 1px solid #00e5ff44; border-radius: 8px;
      padding: 8px 12px; margin-bottom: 8px; font-size: 0.78rem;
    }
    .sync-toggle-box input[type=checkbox] {
      width: 18px; height: 18px; accent-color: #00e5ff; cursor: pointer;
    }
  </style>
</head>
<body>
<div class="container">
  <header>
    <div class="title-area">
      <h1>🏎️ TRUNG TÂM ĐIỀU HÀNH XE ĐUA RACING VLU & RGB LED STUDIO</h1>
      <p>La Bàn Chân Trời IMU • Đo Tốc Độ Max Speed • Đổi Màu Đèn Xi Nhan Đa Sắc • Cloud OTA WiFi</p>
    </div>
    <div class="status-pills">
      <div id="connPill" class="pill offline">● ĐANG CHỜ XE KẾT NỐI WIFI...</div>
      <div id="ipPill" class="pill">IP XE: ---</div>
      <div id="jumpPill" class="pill">NHẢY DỐC: 0 LẦN</div>
    </div>
  </header>

  <!-- NAVIGATION TABS -->
  <div class="nav-bar">
    <button id="navTabRace" class="nav-btn active" onclick="switchMainTab('race')">
      🏎️ TRUNG TÂM ĐUA XE & ĐO TỐC ĐỘ (RACING & IMU)
    </button>
    <button id="navTabLed" class="nav-btn led-tab" onclick="switchMainTab('led')">
      🌈 STUDIO DÀN ĐÈN 6 CỤM (4 XI NHAN + 2 ĐÈN GẦM 30 LED)
    </button>
  </div>

  <!-- =======================================================================
       TAB 1: TRUNG TÂM ĐUA XE & IMU
       ======================================================================= -->
  <div id="tabRaceContent" class="tab-content active">
    <div class="main-grid">
      <!-- Cột trái: Đồng hồ Chân trời nhân tạo & La bàn IMU -->
      <div class="panel hud-box">
        <div class="ptitle" style="width:100%">
          <span>🧭 CHÂN TRỜI NHÂN TẠO & LA BÀN IMU</span>
          <span id="flightStateTxt" style="color:#58a6ff">MẶT ĐẤT</span>
        </div>
        <div class="hud-circle">
          <canvas id="hud" width="600" height="600"></canvas>
        </div>
        <div class="corr-status" id="corrBox">
          TRẠNG THÁI: XE ĐANG ĐỨNG YÊN / CHẠY TRÊN ĐƯỜNG ĐUA
        </div>
        <div class="btn-row" style="width:100%">
          <button class="btn btn-purple" onclick="copyForAI()">📋 COPY DỮ LIỆU IMU GỬI CHO AI</button>
          <button class="btn btn-dark" onclick="zeroIMU()">🎯 ĐẶT ĐIỂM 0° (ZERO)</button>
        </div>
      </div>

      <!-- Cột phải: Thông số, Đồng hồ Tốc độ Max Speed, Tinh chỉnh bay dốc & Cloud OTA -->
      <div class="right-col">
        <div class="panel" style="border-color:#00e5ff66;">
          <div class="ptitle" style="color:#00e5ff;">
            <span>🚀 ĐỒNG HỒ ĐO TỐC ĐỘ & GHI KỶ LỤC MAX SPEED (SPEED CAPTURE)</span>
            <button class="btn btn-purple" style="flex:0;min-width:auto;padding:6px 12px;font-size:0.74rem;" onclick="capSpeedRun()">📸 CHỤP KỶ LỤC TỐC ĐỘ</button>
          </div>
          <div class="cards">
            <div class="card" style="border-color:#00e5ff55;">
              <div class="lbl">Tốc Độ Hiện Tại</div>
              <div class="val" id="vSpd" style="color:#00e5ff">0.0 <span style="font-size:0.8rem">km/h</span></div>
              <div class="sub">Ước lượng Động học + Gia tốc IMU</div>
            </div>
            <div class="card" style="border-color:#3fb95088;background:#0b2117;">
              <div class="lbl">🏆 Kỷ Lục Max Speed</div>
              <div class="val" id="vMaxSpd" style="color:#3fb950">0.0 <span style="font-size:0.8rem">km/h</span></div>
              <div class="sub">Tự động giữ đỉnh tốc độ cao nhất</div>
            </div>
            <div class="card" style="border-color:#ff7b0088;">
              <div class="lbl">✈️ Tốc Độ Lúc Rời Dốc</div>
              <div class="val" id="vJmpSpd" style="color:#ff9900">0.0 <span style="font-size:0.8rem">km/h</span></div>
              <div class="sub">Chốt ngay khoảnh khắc xe cất cánh</div>
            </div>
          </div>
          <div style="margin-top:10px;background:#090d14;height:14px;border-radius:7px;overflow:hidden;border:1px solid #26334d;">
            <div id="spdBar" style="width:0%;height:100%;background:linear-gradient(90deg,#00e5ff,#3fb950,#ffd33d,#ff3333);transition:width 0.08s;"></div>
          </div>
          <div class="srow" style="margin-top:10px;margin-bottom:4px;">
            <label>🔒 Giới hạn Tốc độ tối đa (Speed Cap)</label>
            <input type="range" id="sCap" min="20" max="100" step="5" value="100" oninput="document.getElementById('lCap').innerText=this.value+'% (~'+Math.round(this.value*0.42)+'km/h)'">
            <span id="lCap" style="width:115px">100% (~42km/h)</span>
          </div>
          <div id="capList" style="margin-top:8px;max-height:110px;overflow-y:auto;background:#090d14;border:1px solid #21262d;border-radius:8px;padding:8px;font-family:monospace;font-size:0.75rem;color:#c9d1d9;">
            Chưa có bản ghi tốc độ nào. Khi xe chạy vọt lên >8 km/h rồi phanh dừng lại, Web sẽ TỰ ĐỘNG CAP lại Max Speed từng lượt chạy tại đây (hoặc bấm "📸 CHỤP KỶ LỤC TỐC ĐỘ").
          </div>
        </div>

        <div class="panel">
          <div class="ptitle">📊 THÔNG SỐ GÓC NGHIÊNG & HỘP ĐEN PHÓNG DỐC (BLACKBOX)</div>
          <div class="cards">
            <div class="card">
              <div class="lbl">Mũi Xe (Pitch)</div>
              <div class="val" id="vPitch" style="color:#ff9900">0.0°</div>
              <div class="sub" id="mmPitch">Min: 0.0° | Max: +0.0°</div>
            </div>
            <div class="card">
              <div class="lbl">Nghiêng (Roll)</div>
              <div class="val" id="vRoll" style="color:#58a6ff">0.0°</div>
              <div class="sub" id="mmRoll">Max nghiêng: 0.0°</div>
            </div>
            <div class="card">
              <div class="lbl">La Bàn (Yaw)</div>
              <div class="val" id="vYaw" style="color:#bc8cff">0°</div>
              <div class="sub">Hướng đầu xe</div>
            </div>
            <div class="card">
              <div class="lbl">Trọng Lực (G-Force)</div>
              <div class="val" id="vG" style="color:#3fb950">1.00G</div>
              <div class="sub" id="mmG">Min: 1.00G | Max: 1.00G</div>
            </div>
            <div class="card">
              <div class="lbl">Ga / Xung ESC</div>
              <div class="val" id="vThr" style="color:#ff7b72">0%</div>
              <div class="sub" id="vEsc">1500 µs</div>
            </div>
            <div class="card">
              <div class="lbl">Góc Lái Servo</div>
              <div class="val" id="vStr" style="color:#79c0ff">0%</div>
              <div class="sub" id="vSrv">90°</div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="ptitle">⚡ CLOUD OTA KHÔNG DÂY QUA WIFI (TỐC ĐỘ 3 GIÂY)</div>
          <p style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">
            Xe tự động tải firmware trực tiếp từ máy tính qua mạng WiFi (NguyenNgocTai / NgocTai / Anny) mà không cần kéo cáp USB:
          </p>
          <div class="btn-row">
            <button class="btn btn-green" onclick="triggerInstantOTA()">⚡ NẠP NGAY FILE .BIN HIỆN TẠI QUA WIFI</button>
            <button class="btn btn-blue" onclick="compileAndOTA()">🔨 TỰ BIÊN DỊCH CODE MỚI & NẠP QUA WIFI</button>
          </div>
          <!-- Nút Tắt/Mở Đèn Gầm Nhanh Cho Chế Độ Thi Đấu Ngay Tại Tab Đua Xe -->
          <div id="raceUgBanner" style="margin:10px 0 8px;padding:10px 14px;border-radius:10px;background:#241016;border:1.5px solid #f8514988;display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;">
            <div>
              <div id="raceUgStatusTitle" style="font-size:0.82rem;font-weight:900;color:#ff7b72;">🌈 ĐÈN GẦM 22 LED: ĐANG BẬT (CHẾ ĐỘ BIỂU DIỄN)</div>
              <div id="raceUgStatusSub" style="font-size:0.71rem;color:#c9d1d9;margin-top:2px;">Khi vào sân thi đấu không được bật đèn gầm ➜ Bấm nút bên phải để tắt hẳn & lưu cứng vào xe!</div>
            </div>
            <button id="btnRaceToggleUg" class="btn" style="flex:0;min-width:245px;padding:10px 14px;background:linear-gradient(135deg,#da3633,#f85149);color:#fff;font-weight:900;box-shadow:0 0 14px rgba(248,81,73,0.4);" onclick="setUnderglowCompetitionMode(!(curLedConfig.ug_enabled !== false))">
              🚫 TẮT ĐÈN GẦM (VÀO THI ĐẤU)
            </button>
          </div>
          <div class="btn-row">
            <button class="btn btn-orange" onclick="switchCarToRace()">🏎️ CHUYỂN XE SANG ĐUA TAY CẦM (KÊNH 13)</button>
          </div>
          <div class="ota-log" id="otaLog">Trạng thái OTA: Sẵn sàng</div>
        </div>

        <div class="panel">
          <div class="ptitle">✈️ TINH CHỈNH HỆ THỐNG CÂN BẰNG KHI BAY DỐC (ACTIVE FLIGHT STABILIZER)</div>
          <div class="srow">
            <label>Góc cân bằng mục tiêu (°)</label>
            <input type="range" id="sTp" min="-5" max="15" step="0.5" value="0.0" oninput="document.getElementById('lTp').innerText=this.value+'°'">
            <span id="lTp">0.0°</span>
          </div>
          <div class="srow">
            <label>Ngưỡng G phát hiện bay (Freefall)</label>
            <input type="range" id="sFg" min="0.30" max="0.85" step="0.05" value="0.65" oninput="document.getElementById('lFg').innerText=this.value+'G'">
            <span id="lFg">0.65G</span>
          </div>
          <div class="srow">
            <label>Lực phanh dìm mũi khi vểnh (%)</label>
            <input type="range" id="sBrk" min="-100" max="-15" step="5" value="-85" oninput="document.getElementById('lBrk').innerText=this.value+'%'">
            <span id="lBrk">-85%</span>
          </div>
          <div class="srow">
            <label>Lực bồi ga nhấc mũi khi chúi (%)</label>
            <input type="range" id="sPch" min="20" max="100" step="5" value="85" oninput="document.getElementById('lPch').innerText='+'+this.value+'%'">
            <span id="lPch">+85%</span>
          </div>
          <div class="btn-row">
            <button class="btn btn-green" onclick="applyTune()">💾 CẬP NHẬT THÔNG SỐ BAY DỐC XUỐNG XE</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- =======================================================================
       TAB 2: STUDIO DÀN ĐÈN 6 CỤM WS2812B 5V (30 BÓNG ĐIỀU KHIỂN TỪNG CON LED)
       ======================================================================= -->
  <div id="tabLedContent" class="tab-content">
    <div class="led-grid">
      <!-- Cột trái: Mô phỏng trực quan 30 bóng LED trên 6 cụm của xe -->
      <div class="car-sim-card">
        <div class="ptitle" style="width:100%;color:#00e5ff;margin-bottom:2px;">
          <span>🏎️ MÔ PHỎNG 6 CỤM (30 LED WS2812B)</span>
          <span id="simStatusBadge" style="color:#3fb950;font-size:0.72rem;">30 PIXELS LIVE</span>
        </div>

        <div class="car-chassis-box">
          <!-- Ánh sáng phản chiếu gầm -->
          <div id="fxUnderglow" class="led-underglow-fx"></div>

          <!-- Nhãn thứ tự cụm nối tiếp từ ESP32 GPIO 4 -->
          <div class="cluster-badge b1">Cụm 1: Phải Trước (LED 0,1)</div>
          <div class="cluster-badge b2">Cụm 2: Trái Trước (LED 2,3)</div>
          <div class="cluster-badge b3">Cụm 3: Trái Đuôi (LED 4,5)</div>
          <div class="cluster-badge b4">Cụm 4: Phải Đuôi (LED 6,7)</div>
          <div class="cluster-badge b5">Cụm 5: Gầm Phải 11b (8..18)</div>
          <div class="cluster-badge b6">Cụm 6: Gầm Trái 11b (19..29)</div>

          <!-- CỤM 1: Xi nhan Phải Trước (LED 0, 1) -->
          <div class="turn-cluster c1-fr" title="Cụm 1: Xi Nhan Phải Trước (LED 0, 1)">
            <div id="px0" class="led-pixel-turn"></div>
            <div id="px1" class="led-pixel-turn"></div>
          </div>

          <!-- CỤM 2: Xi nhan Trái Trước (LED 2, 3) -->
          <div class="turn-cluster c2-fl" title="Cụm 2: Xi Nhan Trái Trước (LED 2, 3)">
            <div id="px3" class="led-pixel-turn"></div>
            <div id="px2" class="led-pixel-turn"></div>
          </div>

          <!-- CỤM 3: Xi nhan Trái Đuôi (LED 4, 5) -->
          <div class="turn-cluster c3-rl" title="Cụm 3: Xi Nhan Trái Đuôi (LED 4, 5)">
            <div id="px5" class="led-pixel-turn"></div>
            <div id="px4" class="led-pixel-turn"></div>
          </div>

          <!-- CỤM 4: Xi nhan Phải Đuôi (LED 6, 7) -->
          <div class="turn-cluster c4-rr" title="Cụm 4: Xi Nhan Phải Đuôi (LED 6, 7)">
            <div id="px6" class="led-pixel-turn"></div>
            <div id="px7" class="led-pixel-turn"></div>
          </div>

          <!-- CỤM 5: Đèn Gầm Phải 11 LED (LED 8..18) -->
          <div id="ugRightStrip" class="ug-strip c5-right" title="Cụm 5: Đèn Gầm Phải 11 LED (LED 8..18)"></div>

          <!-- CỤM 6: Đèn Gầm Trái 11 LED (LED 19..29) -->
          <div id="ugLeftStrip" class="ug-strip c6-left" title="Cụm 6: Đèn Gầm Trái 11 LED (LED 19..29)"></div>

          <!-- Hình vẽ xe 2D Top-down Vector SVG -->
          <svg class="car-svg" viewBox="0 0 200 340" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="12" y="34" width="24" height="56" rx="6" fill="#1b2230" stroke="#384966" stroke-width="2"/>
            <rect x="164" y="34" width="24" height="56" rx="6" fill="#1b2230" stroke="#384966" stroke-width="2"/>
            <rect x="12" y="242" width="24" height="62" rx="6" fill="#1b2230" stroke="#384966" stroke-width="2"/>
            <rect x="164" y="242" width="24" height="62" rx="6" fill="#1b2230" stroke="#384966" stroke-width="2"/>
            <path d="M28 62 H172 M28 273 H172" stroke="#384966" stroke-width="4"/>
            <path d="M42 50 C42 25, 158 25, 158 50 L165 180 L158 300 C158 315, 42 315, 42 300 L35 180 Z" fill="#0d1424" stroke="#00e5ff" stroke-width="2.2"/>
            <polygon points="52,110 148,110 140,165 60,165" fill="#162238" stroke="#384966" stroke-width="1.5"/>
            <rect x="66" y="180" width="68" height="70" rx="4" fill="#121b2d" stroke="#243552" stroke-width="1.5"/>
            <rect x="38" y="306" width="124" height="13" rx="3" fill="#ff7b00" opacity="0.85"/>
            <text x="100" y="218" fill="#00e5ff" font-size="10.5" font-weight="900" text-anchor="middle" letter-spacing="1.2">VLU 30-LED</text>
          </svg>
        </div>

        <!-- Sơ đồ đấu nối 6 cụm nối tiếp -->
        <div class="wiring-summary">
          🔌 <b>Thứ tự dây Data từ ESP32 (GPIO 4):</b><br>
          <b>Cụm 1</b> (Phải Trước: 0-1) ➜ <b>Cụm 2</b> (Trái Trước: 2-3) ➜ <b>Cụm 3</b> (Trái Đuôi: 4-5) ➜ <b>Cụm 4</b> (Phải Đuôi: 6-7) ➜ <b>Cụm 5</b> (Gầm Phải 11 bóng: 8-18) ➜ <b>Cụm 6</b> (Gầm Trái 11 bóng: 19-29)
        </div>

        <!-- Bảng nút bấm Test trực tiếp -->
        <button class="btn btn-purple" style="width:100%;padding:11px;font-size:0.8rem;box-shadow:0 0 18px rgba(137,87,229,0.5);" onclick="playStartupIntroNow()">
          🎬 CHẠY THỬ HIỆU ỨNG INTRO MỞ NGUỒN XE (3.6 GIÂY)
        </button>
        <div style="font-size:0.73rem;font-weight:800;color:#8b949e;text-transform:uppercase;">Kiểm tra hiệu ứng trực tiếp trên Web & Xe:</div>
        <div class="test-actions-box">
          <button id="btnTestLeft" onclick="setSimState('left')">◀ RẼ TRÁI (Cụm 2+3)</button>
          <button id="btnTestRight" onclick="setSimState('right')">RẼ PHẢI (Cụm 1+4) ▶</button>
          <button id="btnTestHazard" class="active" onclick="setSimState('hazard')">🚨 HAZARD (Cả 4 Cụm)</button>
          <button id="btnTestDrl" onclick="setSimState('drl')">✨ CHẠY THẲNG (Demi+Gầm)</button>
        </div>
        <!-- Công tắc nhanh Chế Độ Thi Đấu: Tắt / Mở riêng 22 bóng Đèn Gầm & tự lưu vào bộ nhớ xe -->
        <div style="width:100%;padding:9px 10px;border-radius:10px;background:#181022;border:1.5px solid #bc8cff66;">
          <div id="simUgCompLabel" style="font-size:0.73rem;font-weight:900;color:#d2a8ff;text-align:center;margin-bottom:6px;">
            🏁 CHẾ ĐỘ THI ĐẤU (TẮT / BẬT RIÊNG ĐÈN GẦM 22 LED):
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <button id="btnSimUgOff" class="btn" style="min-width:auto;padding:8px 6px;font-size:0.73rem;background:#da3633;color:#fff;" onclick="setUnderglowCompetitionMode(false)">
              🚫 TẮT ĐÈN GẦM (THI ĐẤU)
            </button>
            <button id="btnSimUgOn" class="btn" style="min-width:auto;padding:8px 6px;font-size:0.73rem;background:#238636;color:#fff;" onclick="setUnderglowCompetitionMode(true)">
              🌈 BẬT LẠI ĐÈN GẦM
            </button>
          </div>
        </div>
        <button class="btn btn-dark" style="width:100%;padding:9px;" onclick="setSimState('off_all')">⏹ TẮT TẤT CẢ 30 BÓNG LED</button>
      </div>

      <!-- Cột phải: Bàn xoay màu 360° + Dải quang phổ cầu vồng + 12 Hiệu ứng Xi Nhan + 16 Hiệu ứng Đèn Gầm -->
      <div class="right-col">
        <!-- 1. BẢNG VÒNG TRÒN MÀU 360° & QUANG PHỔ CẦU VỒNG (NHƯ HÌNH GỬI) -->
        <div class="panel" style="border-color:#00e5ff77;">
          <div class="ptitle" style="color:#00e5ff;">
            <span>🎨 BẢNG VÒNG TRÒN MÀU 360° & DẢI QUANG PHỔ CẦU VỒNG (16.7 TRIỆU MÀU)</span>
            <span id="liveSyncBadge" style="font-size:0.72rem;color:#3fb950;">⚡ CHẠM KÉO ĐỔI MÀU TỨC THÌ</span>
          </div>

          <div style="font-size:0.74rem;color:#9ecbff;margin-bottom:8px;">
            <b>Bước 1:</b> Chọn cụm đèn muốn phối màu ở dưới ➜ <b>Bước 2:</b> Xoay <b>Vòng Tròn Màu</b> hoặc kéo trên <b>Bảng Dải Cầu Vồng</b> (như hình bạn gửi):
          </div>

          <!-- 5 Nút chọn vùng đèn đang chỉnh màu -->
          <div class="target-tabs">
            <div id="tabTarget-left" class="target-pill active" onclick="selectColorTarget('left')">
              <div id="dotTarget-left" class="target-dot" style="background:#FFAA00;"></div>
              <div class="target-txt">
                <b>Xi Nhan Trái</b>
                <span>Cụm 2 & Cụm 3 (4 LED)</span>
              </div>
            </div>
            <div id="tabTarget-right" class="target-pill" onclick="selectColorTarget('right')">
              <div id="dotTarget-right" class="target-dot" style="background:#FFAA00;"></div>
              <div class="target-txt">
                <b>Xi Nhan Phải</b>
                <span>Cụm 1 & Cụm 4 (4 LED)</span>
              </div>
            </div>
            <div id="tabTarget-drl" class="target-pill" onclick="selectColorTarget('drl')">
              <div id="dotTarget-drl" class="target-dot" style="background:#00E5FF;"></div>
              <div class="target-txt">
                <b>Đèn Demi Góc</b>
                <span>Nền 4 cụm khi đi thẳng</span>
              </div>
            </div>
            <div id="tabTarget-ug1" class="target-pill" onclick="selectColorTarget('ug1')">
              <div id="dotTarget-ug1" class="target-dot" style="background:#00E5FF;"></div>
              <div class="target-txt">
                <b>Đèn Gầm (Màu 1)</b>
                <span>Cụm 5 & 6 Chính (22 LED)</span>
              </div>
            </div>
            <div id="tabTarget-ug2" class="target-pill" onclick="selectColorTarget('ug2')">
              <div id="dotTarget-ug2" class="target-dot" style="background:#9D00FF;"></div>
              <div class="target-txt">
                <b>Đèn Gầm (Màu 2)</b>
                <span>Màu phối sóng / Lửa / Sao</span>
              </div>
            </div>
          </div>

          <!-- Bàn xoay Vòng Tròn Màu 360° + Bảng Quang Phổ Cầu Vồng 2D (y hệt ảnh gửi) -->
          <div class="color-studio-wrap">
            <!-- Vòng Tròn Màu 360° -->
            <div class="wheel-box" title="Kéo chuột trên Vòng Tròn Màu 360°">
              <canvas id="colorWheelCanvas" width="220" height="220"></canvas>
              <div id="wheelCursor" class="wheel-cursor"></div>
            </div>

            <!-- Bảng Dải Quang Phổ Cầu Vồng 2D (Giống hệt hình bạn gửi) -->
            <div class="spectrum-box-wrap">
              <div class="spectrum-canvas-holder" title="Kéo chuột trên Bảng Dải Cầu Vồng Đa Sắc">
                <canvas id="rainbowSpectrumCanvas" width="460" height="160"></canvas>
                <div id="spectrumCursor" class="spectrum-cursor"></div>
              </div>

              <!-- Thanh chỉnh độ đậm / độ sáng màu + Mã HEX -->
              <div class="srow" style="margin-bottom:0;">
                <label style="width:125px;font-size:0.75rem;">Độ rực màu (Value)</label>
                <input type="range" id="sColorVal" min="15" max="100" value="100" oninput="onColorValSliderChange(this.value)">
                <input type="color" id="nativeColorInput" value="#FFAA00" oninput="applyColorToActiveTarget(this.value, true)" style="width:34px;height:30px;border:none;background:transparent;cursor:pointer;">
                <span id="activeHexDisplay" class="c-hex" style="width:82px;text-align:center;">#FFAA00</span>
              </div>
            </div>
          </div>

          <div class="sync-toggle-box">
            <span>🔗 Khóa đồng bộ màu Xi Nhan Trái & Phải (Chỉnh 1 bên ăn cả 4 cụm xi nhan)</span>
            <input type="checkbox" id="chkSyncSides" checked onchange="toggleSyncSides(this.checked)">
          </div>

          <!-- 12 Màu Mẫu Siêu Xe One-Click -->
          <div style="font-size:0.72rem;font-weight:800;color:#8b949e;text-transform:uppercase;">Chạm chọn nhanh màu Siêu Xe cho vùng đang chọn:</div>
          <div class="swatches-bar">
            <div class="swatch-pill" onclick="applyPreset('#FFAA00')"><div class="swatch-color" style="background:#FFAA00;"></div> Hổ Phách</div>
            <div class="swatch-pill" onclick="applyPreset('#00E5FF')"><div class="swatch-color" style="background:#00E5FF;"></div> Xanh Tron</div>
            <div class="swatch-pill" onclick="applyPreset('#9D00FF')"><div class="swatch-color" style="background:#9D00FF;"></div> Tím Cyber</div>
            <div class="swatch-pill" onclick="applyPreset('#FF1133')"><div class="swatch-color" style="background:#FF1133;"></div> Đỏ Ferrari</div>
            <div class="swatch-pill" onclick="applyPreset('#00FF66')"><div class="swatch-color" style="background:#00FF66;"></div> Xanh Venom</div>
            <div class="swatch-pill" onclick="applyPreset('#FFFFFF')"><div class="swatch-color" style="background:#FFFFFF;"></div> Trắng Băng</div>
            <div class="swatch-pill" onclick="applyPreset('#FFEE00')"><div class="swatch-color" style="background:#FFEE00;"></div> Vàng Lambo</div>
            <div class="swatch-pill" onclick="applyPreset('#FF007F')"><div class="swatch-color" style="background:#FF007F;"></div> Hồng Laser</div>
            <div class="swatch-pill" onclick="applyPreset('#FF5500')"><div class="swatch-color" style="background:#FF5500;"></div> Cam McLaren</div>
            <div class="swatch-pill" onclick="applyPreset('#0055FF')"><div class="swatch-color" style="background:#0055FF;"></div> Xanh Bugatti</div>
            <div class="swatch-pill" onclick="applyPreset('#00FFCC')"><div class="swatch-color" style="background:#00FFCC;"></div> Ngọc Mint</div>
            <div class="swatch-pill" onclick="applyPreset('#FF00FF')"><div class="swatch-color" style="background:#FF00FF;"></div> Tím Neon</div>
          </div>
        </div>

        <!-- 2. KHO 12 HIỆU ỨNG DÀNH RIÊNG CHO 4 CỤM LED XI NHAN (CỤM 1, 2, 3, 4 - 8 LED) -->
        <div class="panel" style="border-color:#ff990066;">
          <div class="ptitle" style="color:#ff9900;">
            <span>🔶 KHO 12 HIỆU ỨNG CHO 4 CỤM LED XI NHAN (CỤM 1, 2, 3, 4 — MỖI CỤM 2 LED)</span>
            <span id="turnPreviewBadge" style="font-size:0.72rem;color:#3fb950;">⚡ Bấm chọn hiệu ứng ➜ Xe chớp thử ngay!</span>
          </div>
          <div class="sync-toggle-box" style="background:#261405;border-color:#ff990088;">
            <span>🔥 <b>Chạy hiệu ứng 4 cụm góc liên tục cả khi đứng yên / đi thẳng</b> (như Đèn Gầm — khi đánh lái rẽ tự tách bên)</span>
            <input type="checkbox" id="chkTurnAlwaysFx" onchange="toggleTurnAlwaysFx(this.checked)">
          </div>
          <div class="sync-toggle-box" style="background:#1c160c;border-color:#ff990044;">
            <span>💡 Bật sáng Đèn Demi ở 4 cụm góc xe khi chạy thẳng (không xi nhan)</span>
            <input type="checkbox" id="chkDrlEnabled" checked onchange="curLedConfig.drl_enabled=this.checked;triggerLivePush()">
          </div>
          <div class="sync-toggle-box" style="background:#0f1c2b;border-color:#58a6ff55;">
            <span>🔄 Đảo ngược chiều Xi Nhan Trái ↔ Phải (Mặc định <b>TẮT</b> đã chuẩn theo thước lái xe — chỉ bật nếu lắp ngược Servo)</span>
            <input type="checkbox" id="chkSwapTurnDir" onchange="curLedConfig.swap_turn_dir=this.checked;triggerLivePush()">
          </div>
          <div class="mode-card-grid">
            <div class="mode-card active" id="modeCard-audi" onclick="setEffectMode('audi', true)">
              <div class="m-icon">🌊</div>
              <div class="m-name">1. Audi Matrix</div>
              <div class="m-desc">Quét đuổi bóng 1 ➜ 2</div>
            </div>
            <div class="mode-card" id="modeCard-standard" onclick="setEffectMode('standard', true)">
              <div class="m-icon">⚡</div>
              <div class="m-name">2. Chớp Chuẩn Đua</div>
              <div class="m-desc">Nháy đồng bộ 2 bóng</div>
            </div>
            <div class="mode-card" id="modeCard-strobe_f1" onclick="setEffectMode('strobe_f1', true)">
              <div class="m-icon">🚨</div>
              <div class="m-name">3. F1 Triple Strobe</div>
              <div class="m-desc">Chớp 3 nhịp siêu tốc F1</div>
            </div>
            <div class="mode-card" id="modeCard-pingpong" onclick="setEffectMode('pingpong', true)">
              <div class="m-icon">🏓</div>
              <div class="m-name">4. Đảo Pha Trong-Ngoài</div>
              <div class="m-desc">Bóng 1 & 2 nháy luân phiên</div>
            </div>
            <div class="mode-card" id="modeCard-front_rear" onclick="setEffectMode('front_rear', true)">
              <div class="m-icon">🔄</div>
              <div class="m-name">5. Đuổi Trước ➜ Đuôi</div>
              <div class="m-desc">Cụm Trước truyền xuống Đuôi</div>
            </div>
            <div class="mode-card" id="modeCard-pulse" onclick="setEffectMode('pulse', true)">
              <div class="m-icon">💓</div>
              <div class="m-name">6. Nhịp Thở Êm</div>
              <div class="m-desc">Sáng mờ dần theo hàm Sin</div>
            </div>
            <div class="mode-card" id="modeCard-heartbeat" onclick="setEffectMode('heartbeat', true)">
              <div class="m-icon">❤️</div>
              <div class="m-name">7. Nhịp Tim Kép</div>
              <div class="m-desc">Đập 2 nhịp Thịch-Thịch</div>
            </div>
            <div class="mode-card" id="modeCard-sparkle" onclick="setEffectMode('sparkle', true)">
              <div class="m-icon">✨</div>
              <div class="m-name">8. Kim Cương Flash</div>
              <div class="m-desc">Chớp hạt trắng Diamond</div>
            </div>
            <div class="mode-card" id="modeCard-police_turn" onclick="setEffectMode('police_turn', true)">
              <div class="m-icon">🚓</div>
              <div class="m-name">9. Cảnh Sát Đuổi Pha</div>
              <div class="m-desc">Chớp Đỏ-Xanh Trước/Sau</div>
            </div>
            <div class="mode-card" id="modeCard-laser_shot" onclick="setEffectMode('laser_shot', true)">
              <div class="m-icon">☄️</div>
              <div class="m-name">10. Phóng Tia Laser</div>
              <div class="m-desc">Bắn tia nhanh có đuôi mờ</div>
            </div>
            <div class="mode-card" id="modeCard-rainbow_turn" onclick="setEffectMode('rainbow_turn', true)">
              <div class="m-icon">🌈</div>
              <div class="m-name">11. Cầu Vồng Rẽ</div>
              <div class="m-desc">Xoay 7 sắc trên cụm rẽ</div>
            </div>
            <div class="mode-card" id="modeCard-plasma_dual" onclick="setEffectMode('plasma_dual', true)">
              <div class="m-icon">🔥</div>
              <div class="m-name">12. Phối 2 Màu Morph</div>
              <div class="m-desc">Trộn màu Xi Nhan & Demi</div>
            </div>
          </div>
          <div class="srow" style="margin-top:12px;">
            <label>Tốc độ hiệu ứng Xi Nhan</label>
            <input type="range" id="sLedSpd" min="80" max="700" step="20" value="280" oninput="document.getElementById('lLedSpd').innerText=this.value+' ms';curLedConfig.speed_ms=parseInt(this.value);" onchange="triggerTurnSpeedPreview()">
            <span id="lLedSpd">280 ms</span>
          </div>
        </div>

        <!-- 3. KHO 16 HIỆU ỨNG SIÊU XỊN DÀNH RIÊNG CHO 2 CỤM ĐÈN GẦM (CỤM 5 & 6 — 22 LED) -->
        <div class="panel" id="ugMainPanel" style="border-color:#bc8cff88;">
          <div class="ptitle" style="color:#d2a8ff;">
            <span>🌌 KHO 16 HIỆU ỨNG ĐỘC LẬP CHO 2 CỤM ĐÈN GẦM (CỤM 5 PHẢI 11 LED + CỤM 6 TRÁI 11 LED)</span>
            <span id="ugHeaderBadge" style="font-size:0.72rem;color:#3fb950;">22 Bóng Gầm Đang Bật</span>
          </div>

          <!-- Hộp Công Tắc Tắt/Mở Đèn Gầm Khi Vào Thi Đấu (Tự Lưu NVS Xuống Xe Tức Thì) -->
          <div id="ugCompetitionBox" style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:10px 12px;margin-bottom:8px;border-radius:10px;background:#241016;border:1.5px solid #f8514977;">
            <div>
              <div id="ugCompBoxTitle" style="font-size:0.8rem;font-weight:900;color:#ff7b72;">🏁 CÔNG TẮC THI ĐẤU: ĐÈN GẦM ĐANG BẬT SÁNG</div>
              <div style="font-size:0.7rem;color:#c9d1d9;margin-top:2px;">Bấm <b>"🚫 TẮT HẲN ĐÈN GẦM"</b> trước khi vào thi đấu ➜ Tắt sạch cả khi mới mở nguồn Intro & tự lưu cứng vào xe!</div>
            </div>
            <button id="btnPanelToggleUg" class="btn" style="flex:0;min-width:215px;padding:9px 12px;background:linear-gradient(135deg,#da3633,#f85149);color:#fff;font-weight:900;" onclick="setUnderglowCompetitionMode(!(curLedConfig.ug_enabled !== false))">
              🚫 TẮT HẲN ĐÈN GẦM (THI ĐẤU)
            </button>
          </div>

          <div class="sync-toggle-box" style="background:#191229;border-color:#bc8cff44;">
            <span>🌟 Cho phép bật hệ thống 2 Cụm Đèn Gầm 22 LED (Bỏ tích = Tắt hẳn Đèn Gầm khi thi đấu)</span>
            <input type="checkbox" id="chkUgEnabled" checked onchange="setUnderglowCompetitionMode(this.checked)">
          </div>
          <div class="sync-toggle-box" style="background:#141a29;border-color:#58a6ff44;">
            <span>🔄 Đảo chiều chạy Cụm 6 (Gầm Trái 19..29) để 2 bên gầm chạy cùng chiều Đầu ➜ Đuôi</span>
            <input type="checkbox" id="chkUgRevLeft" onchange="curLedConfig.ug_rev_left=this.checked;triggerLivePush()">
          </div>

          <div class="mode-card-grid" id="ugCardsGrid">
            <div class="mode-card ug-card active" id="ugCard-neon_cyber" onclick="setUgEffectMode('neon_cyber')">
              <div class="m-icon">🌈</div>
              <div class="m-name">1. Cầu Vồng Dọc Xe</div>
              <div class="m-desc">Trượt 7 sắc dọc 11 bóng</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-knight_rider" onclick="setUgEffectMode('knight_rider')">
              <div class="m-icon">🏎️</div>
              <div class="m-name">2. Mắt Thần K.I.T.T</div>
              <div class="m-desc">Tia quét Đầu ↔ Đuôi</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-meteor_rain" onclick="setUgEffectMode('meteor_rain')">
              <div class="m-icon">☄️</div>
              <div class="m-name">3. Mưa Sao Băng</div>
              <div class="m-desc">Sao băng trắng phóng dọc</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-dual_flow" onclick="setUgEffectMode('dual_flow')">
              <div class="m-icon">🌊</div>
              <div class="m-name">4. Sóng Đôi 2 Màu</div>
              <div class="m-desc">Cuộn sóng Màu Gầm 1 & 2</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-center_burst" onclick="setUgEffectMode('center_burst')">
              <div class="m-icon">💥</div>
              <div class="m-name">5. Bung Tỏa Từ Tâm</div>
              <div class="m-desc">Giữa gầm nổ sóng ra 2 đầu</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-converge_in" onclick="setUgEffectMode('converge_in')">
              <div class="m-icon">🌀</div>
              <div class="m-name">6. Hội Tụ Về Tâm</div>
              <div class="m-desc">2 đầu lao vào giữa gầm</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-nitro_flame" onclick="setUgEffectMode('nitro_flame')">
              <div class="m-icon">🔥</div>
              <div class="m-name">7. Lửa Nitro Bô Xe</div>
              <div class="m-desc">Ngọn lửa bập bùng 11 LED</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-police_pursuit" onclick="setUgEffectMode('police_pursuit')">
              <div class="m-icon">🚓</div>
              <div class="m-name">8. Cảnh Sát Đặc Nhiệm</div>
              <div class="m-desc">Quét Đỏ-Xanh-Trắng 2 sườn</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-throttle_react" onclick="setUgEffectMode('throttle_react')">
              <div class="m-icon">🚀</div>
              <div class="m-name">9. Cảm Ứng Theo Ga</div>
              <div class="m-desc">Bóp ga càng lớn chạy càng gắt</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-galaxy_twinkle" onclick="setUgEffectMode('galaxy_twinkle')">
              <div class="m-icon">✨</div>
              <div class="m-name">10. Ngân Hà Lấp Lánh</div>
              <div class="m-desc">Hạt sao trắng trên nền Neon</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-breathing_sync" onclick="setUgEffectMode('breathing_sync')">
              <div class="m-icon">💓</div>
              <div class="m-name">11. Nhịp Thở Đổi Sắc</div>
              <div class="m-desc">Thở êm giữa Màu 1 & Màu 2</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-theater_chase" onclick="setUgEffectMode('theater_chase')">
              <div class="m-icon">🎪</div>
              <div class="m-name">12. Đuổi Hạt Cyber</div>
              <div class="m-desc">Chuỗi hạt 3 bóng rượt đuổi</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-strobe_matrix" onclick="setUgEffectMode('strobe_matrix')">
              <div class="m-icon">⚡</div>
              <div class="m-name">13. Chớp Ma Trận Drift</div>
              <div class="m-desc">Nháy phân đoạn 4 bóng</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-ocean_aurora" onclick="setUgEffectMode('ocean_aurora')">
              <div class="m-icon">🌌</div>
              <div class="m-name">14. Cực Quang Aurora</div>
              <div class="m-desc">Sóng lượn đa tầng biến ảo</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-turn_sync_ug" onclick="setUgEffectMode('turn_sync_ug')">
              <div class="m-icon">🔗</div>
              <div class="m-name">15. Gầm Đuổi Xi Nhan</div>
              <div class="m-desc">Rẽ bên nào gầm bên đó chạy tia</div>
            </div>
            <div class="mode-card ug-card" id="ugCard-solid_neon" onclick="setUgEffectMode('solid_neon')">
              <div class="m-icon">💡</div>
              <div class="m-name">16. Đèn Ống Neon Tĩnh</div>
              <div class="m-desc">Sáng mịn Gradient Fast&Furious</div>
            </div>
          </div>

          <div class="srow" style="margin-top:12px;">
            <label>Tốc độ chạy hiệu ứng Đèn Gầm</label>
            <input type="range" id="sUgSpd" min="60" max="700" step="20" value="240" oninput="document.getElementById('lUgSpd').innerText=this.value+' ms';curLedConfig.ug_speed_ms=parseInt(this.value);" onchange="triggerLivePush()">
            <span id="lUgSpd">240 ms</span>
          </div>
          <div class="srow">
            <label>Độ sáng riêng của 2 Cụm Gầm</label>
            <input type="range" id="sUgBr" min="15" max="100" step="5" value="85" oninput="document.getElementById('lUgBr').innerText=this.value+'%';curLedConfig.ug_brightness=parseInt(this.value);" onchange="triggerLivePush()">
            <span id="lUgBr">85%</span>
          </div>
        </div>

        <!-- 3B. KHO 8 KỊCH BẢN INTRO CHÀO MỪNG KHI MỚI MỞ NGUỒN XE (WELCOME LIGHT SHOW) -->
        <div class="panel" style="border-color:#3fb95088;">
          <div class="ptitle" style="color:#3fb950;">
            <span>🎬 KHO 8 KỊCH BẢN INTRO CHÀO MỪNG KHI MỚI MỞ NGUỒN XE (POWER-ON WELCOME SHOW)</span>
            <button class="btn btn-green" style="flex:0;min-width:auto;padding:5px 12px;font-size:0.72rem;" onclick="playStartupIntroNow()">▶️ TEST INTRO NGAY</button>
          </div>

          <div class="sync-toggle-box" style="background:#0d2116;border-color:#3fb95055;">
            <span>🚀 Tự động trình diễn Intro 30 LED mỗi khi bật công tắc nguồn xe</span>
            <input type="checkbox" id="chkIntroEnabled" checked onchange="curLedConfig.intro_enabled=this.checked;triggerLivePush()">
          </div>

          <div class="mode-card-grid">
            <div class="mode-card intro-card active" id="introCard-audi_rs" onclick="setIntroMode('audi_rs')">
              <div class="m-icon">🏆</div>
              <div class="m-name">1. Audi RS Matrix</div>
              <div class="m-desc">Chớp băng 4 góc ➜ Quét gầm & mở rèm</div>
            </div>
            <div class="mode-card intro-card" id="introCard-cyber_ignite" onclick="setIntroMode('cyber_ignite')">
              <div class="m-icon">⚡</div>
              <div class="m-name">2. Cyberpunk Boot</div>
              <div class="m-desc">Glitch 4 góc ➜ Nạp thanh pin 0..100%</div>
            </div>
            <div class="mode-card intro-card" id="introCard-lambo_v12" onclick="setIntroMode('lambo_v12')">
              <div class="m-icon">🔥</div>
              <div class="m-name">3. Lambo V12 Ignite</div>
              <div class="m-desc">Nhịp tim Đỏ ➜ Đề nổ khè lửa pô V12</div>
            </div>
            <div class="mode-card intro-card" id="introCard-knight_scanner" onclick="setIntroMode('knight_scanner')">
              <div class="m-icon">🏎️</div>
              <div class="m-name">4. K.I.T.T Scanner</div>
              <div class="m-desc">Quét vòng 4 góc + 2 mắt thần ngược chiều</div>
            </div>
            <div class="mode-card intro-card" id="introCard-f1_countdown" onclick="setIntroMode('f1_countdown')">
              <div class="m-icon">🚦</div>
              <div class="m-name">5. Đèn Xuất Phát F1</div>
              <div class="m-desc">Đếm 5 nấc Đỏ ➜ Tắt phụt ➜ Bùng Xanh Lá!</div>
            </div>
            <div class="mode-card intro-card" id="introCard-galaxy_supernova" onclick="setIntroMode('galaxy_supernova')">
              <div class="m-icon">🌌</div>
              <div class="m-name">6. Vụ Nổ Siêu Tân Tinh</div>
              <div class="m-desc">Hút về tâm gầm ➜ Nén lõi ➜ Nổ 7 sắc</div>
            </div>
            <div class="mode-card intro-card" id="introCard-police_vip" onclick="setIntroMode('police_vip')">
              <div class="m-icon">🚓</div>
              <div class="m-name">7. Hộ Tống Đặc Nhiệm</div>
              <div class="m-desc">Chớp dẫn đoàn Đỏ-Xanh-Trắng đảo chéo</div>
            </div>
            <div class="mode-card intro-card" id="introCard-royal_gold" onclick="setIntroMode('royal_gold')">
              <div class="m-icon">👑</div>
              <div class="m-name">8. Hoàng Gia Maybach</div>
              <div class="m-desc">Mở rèm lụa Vàng Hoàng Kim & Ngọc Trai</div>
            </div>
          </div>
        </div>

        <!-- 4. ĐỘ SÁNG TỔNG & LƯU VÀO BỘ NHỚ NVS CỦA XE -->
        <div class="panel">
          <div class="ptitle">⚙️ ĐỘ SÁNG TỔNG 30 LED & LƯU VÀO BỘ NHỚ TRÊN XE</div>
          <div class="srow">
            <label>Độ sáng tổng toàn xe (Master)</label>
            <input type="range" id="sLedBr" min="15" max="100" step="5" value="90" oninput="document.getElementById('lLedBr').innerText=this.value+'%';curLedConfig.brightness=parseInt(this.value);" onchange="triggerLivePush()">
            <span id="lLedBr">90%</span>
          </div>

          <div class="btn-row" style="margin-top:12px;">
            <button class="btn btn-green" onclick="saveAndApplyLedConfig()">💾 LƯU CẤU HÌNH 6 CỤM LED & GỬI XUỐNG XE</button>
            <button class="btn btn-dark" onclick="resetLedDefault()">🔄 KHÔI PHỤC MẶC ĐỊNH</button>
          </div>
          <div class="ota-log" id="ledStatusLog">Trạng thái: Sẵn sàng điều khiển 6 cụm (30 bóng WS2812B)!</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
  const UG_LEN = 11;
  const IDX_R_UG = 8;
  const IDX_L_UG = 19;
  const NUM_LEDS_TOTAL = 30;

  // Khởi tạo 22 bóng LED Gầm trên giao diện mô phỏng (Cụm 5: px8..px18, Cụm 6: px19..px29)
  function buildUnderglowDOM() {
    const rStrip = document.getElementById('ugRightStrip');
    const lStrip = document.getElementById('ugLeftStrip');
    if (rStrip && rStrip.children.length === 0) {
      for (let i = 0; i < UG_LEN; i++) {
        const d = document.createElement('div');
        d.id = 'px' + (IDX_R_UG + i);
        d.className = 'led-pixel-ug';
        d.title = `Cụm 5 - Gầm Phải: LED #${IDX_R_UG + i}`;
        rStrip.appendChild(d);
      }
    }
    if (lStrip && lStrip.children.length === 0) {
      for (let i = 0; i < UG_LEN; i++) {
        const d = document.createElement('div');
        d.id = 'px' + (IDX_L_UG + i);
        d.className = 'led-pixel-ug';
        d.title = `Cụm 6 - Gầm Trái: LED #${IDX_L_UG + i}`;
        lStrip.appendChild(d);
      }
    }
  }
  buildUnderglowDOM();

  // Chuyển Tab chính: 'race' hoặc 'led'
  function switchMainTab(tab) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    if (tab === 'led') {
      document.getElementById('navTabLed').classList.add('active');
      document.getElementById('tabLedContent').classList.add('active');
      initColorCanvases();
      startLedSimulator();
    } else {
      document.getElementById('navTabRace').classList.add('active');
      document.getElementById('tabRaceContent').classList.add('active');
    }
  }

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('tab') === 'led') {
    switchMainTab('led');
  }

  // =========================================================================
  // CẤU HÌNH & BỘ CHỌN MÀU VÒNG TRÒN 360° + BẢNG QUANG PHỔ CẦU VỒNG 2D
  // =========================================================================
  let curLedConfig = {
    left_color: '#FFAA00',
    right_color: '#FFAA00',
    drl_color: '#00E5FF',
    sync_sides: true,
    mode: 'audi',
    brightness: 90,
    speed_ms: 280,
    drl_enabled: true,
    turn_always_fx: false,
    swap_turn_dir: false,
    ug_color1: '#00E5FF',
    ug_color2: '#9D00FF',
    ug_mode: 'neon_cyber',
    ug_speed_ms: 240,
    ug_brightness: 85,
    ug_enabled: true,
    ug_rev_left: false,
    intro_mode: 'audi_rs',
    intro_enabled: true
  };

  let activeColorTarget = 'left'; // 'left', 'right', 'drl', 'ug1', 'ug2'
  let curHSV = { h: 40, s: 100, v: 100 };
  let livePushTimeout = null;

  function hsvToHex(h, s, v) {
    s /= 100; v /= 100;
    const c = v * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = v - c;
    let r = 0, g = 0, b = 0;
    if (0 <= h && h < 60)   { r = c; g = x; b = 0; }
    else if (60 <= h && h < 120)  { r = x; g = c; b = 0; }
    else if (120 <= h && h < 180) { r = 0; g = c; b = x; }
    else if (180 <= h && h < 240) { r = 0; g = x; b = c; }
    else if (240 <= h && h < 300) { r = x; g = 0; b = c; }
    else { r = c; g = 0; b = x; }
    const toHex = n => Math.round((n + m) * 255).toString(16).padStart(2, '0');
    return ('#' + toHex(r) + toHex(g) + toHex(b)).toUpperCase();
  }

  function hexToRgb(hex) {
    let s = (hex || '#FFAA00').replace('#', '').trim();
    if (s.length !== 6) s = 'FFAA00';
    const num = parseInt(s, 16);
    return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
  }

  function rgbToHex(r, g, b) {
    const h = n => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0');
    return ('#' + h(r) + h(g) + h(b)).toUpperCase();
  }

  function scaleHex(hex, scale0to255) {
    const { r, g, b } = hexToRgb(hex);
    return rgbToHex((r * scale0to255) >> 8, (g * scale0to255) >> 8, (b * scale0to255) >> 8);
  }

  function blendHex(hex1, hex2, t0to255) {
    const c1 = hexToRgb(hex1), c2 = hexToRgb(hex2);
    const r = c1.r + (((c2.r - c1.r) * t0to255) >> 8);
    const g = c1.g + (((c2.g - c1.g) * t0to255) >> 8);
    const b = c1.b + (((c2.b - c1.b) * t0to255) >> 8);
    return rgbToHex(r, g, b);
  }

  // Vẽ Vòng Tròn Màu 360° & Bảng Dải Quang Phổ Cầu Vồng 2D (như hình user gửi)
  let canvasesInitialized = false;
  function initColorCanvases() {
    const wheel = document.getElementById('colorWheelCanvas');
    const spec  = document.getElementById('rainbowSpectrumCanvas');
    if (!wheel || !spec) return;

    // 1. Vẽ Vòng Tròn Màu 360°
    const wCtx = wheel.getContext('2d');
    const wR = wheel.width / 2;
    wCtx.clearRect(0, 0, wheel.width, wheel.height);
    for (let angle = 0; angle < 360; angle += 1) {
      const startAngle = (angle - 1) * Math.PI / 180;
      const endAngle   = (angle + 1) * Math.PI / 180;
      wCtx.beginPath();
      wCtx.moveTo(wR, wR);
      wCtx.arc(wR, wR, wR, startAngle, endAngle);
      wCtx.closePath();
      const grad = wCtx.createRadialGradient(wR, wR, 0, wR, wR, wR);
      grad.addColorStop(0, '#FFFFFF');
      grad.addColorStop(1, `hsl(${angle}, 100%, 50%)`);
      wCtx.fillStyle = grad;
      wCtx.fill();
    }

    // 2. Vẽ Bảng Quang Phổ Cầu Vồng 2D (Giống hệt hình ảnh bạn gửi!)
    const sCtx = spec.getContext('2d');
    const sW = spec.width, sH = spec.height;
    const hGrad = sCtx.createLinearGradient(0, 0, sW, 0);
    hGrad.addColorStop(0.00, '#FF0000');
    hGrad.addColorStop(0.15, '#FFFF00');
    hGrad.addColorStop(0.33, '#00FF00');
    hGrad.addColorStop(0.50, '#00FFFF');
    hGrad.addColorStop(0.67, '#0000FF');
    hGrad.addColorStop(0.84, '#9D00FF');
    hGrad.addColorStop(1.00, '#FF00AA');
    sCtx.fillStyle = hGrad;
    sCtx.fillRect(0, 0, sW, sH);

    // Phủ lớp chuyển sắc trắng mềm từ dưới lên như hình mẫu
    const vGrad = sCtx.createLinearGradient(0, 0, 0, sH);
    vGrad.addColorStop(0.0, 'rgba(255,255,255,0)');
    vGrad.addColorStop(0.65, 'rgba(255,255,255,0.18)');
    vGrad.addColorStop(1.0, 'rgba(255,255,255,0.88)');
    sCtx.fillStyle = vGrad;
    sCtx.fillRect(0, 0, sW, sH);

    if (canvasesInitialized) return;
    canvasesInitialized = true;

    // Sự kiện kéo chuột / cảm ứng trên Vòng Tròn Màu 360°
    let draggingWheel = false;
    function pickFromWheel(e) {
      const rect = wheel.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const cx = rect.width / 2, cy = rect.height / 2;
      const dx = clientX - rect.left - cx;
      const dy = clientY - rect.top - cy;
      const dist = Math.min(cx, Math.sqrt(dx * dx + dy * dy));
      let deg = Math.atan2(dy, dx) * 180 / Math.PI;
      if (deg < 0) deg += 360;

      curHSV.h = deg;
      curHSV.s = Math.round((dist / cx) * 100);
      curHSV.v = parseInt(document.getElementById('sColorVal').value) || 100;

      const curEl = document.getElementById('wheelCursor');
      const rad = deg * Math.PI / 180;
      curEl.style.left = (cx + Math.cos(rad) * dist) + 'px';
      curEl.style.top  = (cy + Math.sin(rad) * dist) + 'px';

      const hex = hsvToHex(curHSV.h, curHSV.s, curHSV.v);
      curEl.style.background = hex;
      applyColorToActiveTarget(hex, true);
    }
    wheel.addEventListener('mousedown', e => { draggingWheel = true; pickFromWheel(e); });
    window.addEventListener('mousemove', e => { if (draggingWheel) pickFromWheel(e); });
    window.addEventListener('mouseup', () => { draggingWheel = false; });
    wheel.addEventListener('touchstart', e => { draggingWheel = true; pickFromWheel(e); e.preventDefault(); }, {passive:false});
    wheel.addEventListener('touchmove', e => { if (draggingWheel) pickFromWheel(e); e.preventDefault(); }, {passive:false});
    wheel.addEventListener('touchend', () => { draggingWheel = false; });

    // Sự kiện kéo chuột / cảm ứng trên Bảng Dải Quang Phổ Cầu Vồng 2D
    let draggingSpec = false;
    function pickFromSpectrum(e) {
      const rect = spec.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const x = Math.max(0, Math.min(rect.width, clientX - rect.left));
      const y = Math.max(0, Math.min(rect.height, clientY - rect.top));

      curHSV.h = (x / rect.width) * 330; // Đỏ -> Tím Hồng
      curHSV.s = Math.round((1 - (y / rect.height) * 0.85) * 100);
      curHSV.v = parseInt(document.getElementById('sColorVal').value) || 100;

      const curEl = document.getElementById('spectrumCursor');
      curEl.style.left = x + 'px';
      curEl.style.top  = y + 'px';

      const hex = hsvToHex(curHSV.h, curHSV.s, curHSV.v);
      curEl.style.background = hex;
      applyColorToActiveTarget(hex, true);
    }
    spec.addEventListener('mousedown', e => { draggingSpec = true; pickFromSpectrum(e); });
    window.addEventListener('mousemove', e => { if (draggingSpec) pickFromSpectrum(e); });
    window.addEventListener('mouseup', () => { draggingSpec = false; });
    spec.addEventListener('touchstart', e => { draggingSpec = true; pickFromSpectrum(e); e.preventDefault(); }, {passive:false});
    spec.addEventListener('touchmove', e => { if (draggingSpec) pickFromSpectrum(e); e.preventDefault(); }, {passive:false});
    spec.addEventListener('touchend', () => { draggingSpec = false; });
  }

  function onColorValSliderChange(val) {
    curHSV.v = parseInt(val) || 100;
    const hex = hsvToHex(curHSV.h, curHSV.s, curHSV.v);
    applyColorToActiveTarget(hex, true);
  }

  function selectColorTarget(target) {
    activeColorTarget = target;
    document.querySelectorAll('.target-pill').forEach(el => el.classList.remove('active'));
    const tab = document.getElementById('tabTarget-' + target);
    if (tab) tab.classList.add('active');

    let hex = '#FFAA00';
    if (target === 'left') hex = curLedConfig.left_color;
    else if (target === 'right') hex = curLedConfig.right_color;
    else if (target === 'drl') hex = curLedConfig.drl_color;
    else if (target === 'ug1') hex = curLedConfig.ug_color1;
    else if (target === 'ug2') hex = curLedConfig.ug_color2;

    document.getElementById('activeHexDisplay').innerText = hex.toUpperCase();
    document.getElementById('nativeColorInput').value = hex;
  }

  function applyColorToActiveTarget(hex, doLivePush) {
    hex = hex.toUpperCase();
    document.getElementById('activeHexDisplay').innerText = hex;
    document.getElementById('nativeColorInput').value = hex;

    if (activeColorTarget === 'left') {
      curLedConfig.left_color = hex;
      document.getElementById('dotTarget-left').style.background = hex;
      if (curLedConfig.sync_sides) {
        curLedConfig.right_color = hex;
        document.getElementById('dotTarget-right').style.background = hex;
      }
    } else if (activeColorTarget === 'right') {
      curLedConfig.right_color = hex;
      document.getElementById('dotTarget-right').style.background = hex;
      if (curLedConfig.sync_sides) {
        curLedConfig.left_color = hex;
        document.getElementById('dotTarget-left').style.background = hex;
      }
    } else if (activeColorTarget === 'drl') {
      curLedConfig.drl_color = hex;
      document.getElementById('dotTarget-drl').style.background = hex;
    } else if (activeColorTarget === 'ug1') {
      curLedConfig.ug_color1 = hex;
      document.getElementById('dotTarget-ug1').style.background = hex;
    } else if (activeColorTarget === 'ug2') {
      curLedConfig.ug_color2 = hex;
      document.getElementById('dotTarget-ug2').style.background = hex;
    }

    if (doLivePush) {
      if (activeColorTarget === 'left' || activeColorTarget === 'right') {
        const pAct = curLedConfig.turn_always_fx ? null : (curLedConfig.sync_sides ? 'hazard' : activeColorTarget);
        triggerLivePush(pAct);
      } else {
        triggerLivePush();
      }
    }
  }

  let pendingPreviewAct = null;
  function triggerLivePush(previewAct = null, immediate = false) {
    if (previewAct) pendingPreviewAct = previewAct;
    if (livePushTimeout) clearTimeout(livePushTimeout);
    livePushTimeout = setTimeout(() => {
      const payload = Object.assign({}, curLedConfig, { live: true });
      if (pendingPreviewAct) {
        payload.preview_act = pendingPreviewAct;
        pendingPreviewAct = null;
      }
      fetch('/api/xedua/led', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      }).catch(()=>{});
    }, immediate ? 15 : 110);
  }

  function getTurnPreviewAction() {
    if (curLedConfig.turn_always_fx) return null;
    if (simActiveState === 'left' || simActiveState === 'right' || simActiveState === 'hazard') return simActiveState;
    return 'hazard';
  }

  function triggerTurnSpeedPreview() {
    simIntroPlaying = false;
    if (!curLedConfig.turn_always_fx && (simActiveState === 'drl' || simActiveState === 'off_all')) {
      simActiveState = 'hazard';
      document.getElementById('btnTestHazard').classList.add('active');
      document.getElementById('btnTestDrl').classList.remove('active');
    }
    triggerLivePush(getTurnPreviewAction(), true);
  }

  async function toggleTurnAlwaysFx(checked) {
    curLedConfig.turn_always_fx = !!checked;
    const badge = document.getElementById('turnPreviewBadge');
    if (badge) {
      badge.innerText = checked ? '🔥 ĐANG CHẠY LIÊN TỤC 4 CỤM GÓC!' : '⚡ Bấm chọn hiệu ứng ➜ Xe chớp thử ngay!';
      badge.style.color = checked ? '#ff9900' : '#3fb950';
    }
    const payload = Object.assign({}, curLedConfig, { preview_act: checked ? 'hazard' : 'off' });
    try {
      const res = await fetch('/api/xedua/led', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      const logEl = document.getElementById('ledStatusLog');
      if (logEl) {
        logEl.innerText = (checked ? '🔥 ĐÃ BẬT CHẠY LIÊN TỤC 4 CỤM GÓC: ' : '🔶 ĐÃ TRẢ VỀ CHẾ ĐỘ XI NHAN KHI RẼ: ') + data.message;
        logEl.style.color = '#ff9900';
      }
    } catch (e) {}
  }

  function applyPreset(hex) {
    applyColorToActiveTarget(hex, true);
  }

  function toggleSyncSides(val) {
    curLedConfig.sync_sides = val;
    if (val) {
      curLedConfig.right_color = curLedConfig.left_color;
      document.getElementById('dotTarget-right').style.background = curLedConfig.left_color;
      triggerLivePush();
    }
  }

  function setEffectMode(mode, userClicked = false) {
    curLedConfig.mode = mode;
    document.querySelectorAll('.mode-card:not(.ug-card):not(.intro-card)').forEach(c => c.classList.remove('active'));
    const target = document.getElementById('modeCard-' + mode);
    if (target) target.classList.add('active');

    if (userClicked) {
      simIntroPlaying = false;
      if (!curLedConfig.turn_always_fx && (simActiveState === 'drl' || simActiveState === 'off_all')) {
        simActiveState = 'hazard';
        document.getElementById('btnTestLeft').classList.remove('active');
        document.getElementById('btnTestRight').classList.remove('active');
        document.getElementById('btnTestHazard').classList.add('active');
        document.getElementById('btnTestDrl').classList.remove('active');
      }
      const pAct = getTurnPreviewAction();
      triggerLivePush(pAct, true);
      const logEl = document.getElementById('ledStatusLog');
      if (logEl) {
        logEl.innerText = curLedConfig.turn_always_fx
          ? `🔥 Đang chạy liên tục hiệu ứng [${mode}] trên cả 4 cụm góc xe!`
          : `🔶 Đang phát thử trực tiếp hiệu ứng Xi Nhan [${mode}] trên 4 cụm góc xe thật (20 giây — đánh lái tự tắt)!`;
        logEl.style.color = '#ff9900';
      }
    }
  }

  function setUgEffectMode(ugMode) {
    curLedConfig.ug_mode = ugMode;
    document.querySelectorAll('.mode-card.ug-card').forEach(c => c.classList.remove('active'));
    const target = document.getElementById('ugCard-' + ugMode);
    if (target) target.classList.add('active');
    triggerLivePush();
  }

  function setIntroMode(inMode) {
    curLedConfig.intro_mode = inMode;
    document.querySelectorAll('.mode-card.intro-card').forEach(c => c.classList.remove('active'));
    const target = document.getElementById('introCard-' + inMode);
    if (target) target.classList.add('active');
    simIntroPlaying = true;
    simIntroStartMs = Date.now();
    triggerLivePush();
  }

  let simActiveState = 'hazard'; // 'left', 'right', 'hazard', 'drl', 'off_all'
  let simTimer = null;
  let simIntroPlaying = false;
  let simIntroStartMs = 0;

  function playStartupIntroNow() {
    simIntroPlaying = true;
    simIntroStartMs = Date.now();
    fetch('/api/xedua/led/test', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: 'intro', intro_mode: curLedConfig.intro_mode || 'audi_rs'})
    }).then(r => r.json()).then(res => {
      const st = document.getElementById('ledStatusLog');
      if (st) {
        st.innerText = '🎬 Đang chạy hiệu ứng Intro mở nguồn (' + (curLedConfig.intro_mode || 'audi_rs') + ') trên 30 LED của xe & mô phỏng 2D!';
        st.style.color = '#3fb950';
      }
    }).catch(()=>{});
  }

  function setSimState(st) {
    simIntroPlaying = false;
    simActiveState = st;
    document.getElementById('btnTestLeft').classList.toggle('active', st === 'left');
    document.getElementById('btnTestRight').classList.toggle('active', st === 'right');
    document.getElementById('btnTestHazard').classList.toggle('active', st === 'hazard');
    document.getElementById('btnTestDrl').classList.toggle('active', st === 'drl');

    fetch('/api/xedua/led/test', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: st})
    }).catch(()=>{});
  }

  function refreshUnderglowCompetitionUI() {
    const ugOn = (curLedConfig.ug_enabled !== false);
    const chkUg = document.getElementById('chkUgEnabled');
    if (chkUg) chkUg.checked = ugOn;

    // 1. Cập nhật Banner Chế Độ Thi Đấu ở Tab 1 (Trung Tâm Đua Xe)
    const raceBanner = document.getElementById('raceUgBanner');
    const raceTitle  = document.getElementById('raceUgStatusTitle');
    const raceSub    = document.getElementById('raceUgStatusSub');
    const raceBtn    = document.getElementById('btnRaceToggleUg');
    if (raceBanner && raceTitle && raceBtn) {
      if (ugOn) {
        raceBanner.style.background  = '#241016';
        raceBanner.style.borderColor = '#f8514988';
        raceTitle.style.color        = '#ff7b72';
        raceTitle.innerText          = '🌈 ĐÈN GẦM 22 LED: ĐANG BẬT (CHẾ ĐỘ BIỂU DIỄN)';
        if (raceSub) raceSub.innerText = 'Khi vào sân thi đấu không được bật đèn gầm ➜ Bấm nút bên phải để tắt hẳn & lưu cứng vào xe!';
        raceBtn.style.background     = 'linear-gradient(135deg,#da3633,#f85149)';
        raceBtn.innerText            = '🚫 TẮT ĐÈN GẦM (VÀO THI ĐẤU)';
      } else {
        raceBanner.style.background  = '#0c2418';
        raceBanner.style.borderColor = '#3fb95099';
        raceTitle.style.color        = '#3fb950';
        raceTitle.innerText          = '✅ CHẾ ĐỘ THI ĐẤU: ĐÃ TẮT HẲN ĐÈN GẦM 22 LED (HỢP LỆ)';
        if (raceSub) raceSub.innerText = 'Toàn bộ 22 bóng đèn gầm đã khóa tắt 100% (kể cả khi tắt/mở nguồn xe ở vạch xuất phát).';
        raceBtn.style.background     = 'linear-gradient(135deg,#1f6feb,#58a6ff)';
        raceBtn.innerText            = '🌈 BẬT LẠI ĐÈN GẦM (SAU KHI ĐUA)';
      }
    }

    // 2. Cập nhật Cụm Nút Nhanh dưới Mô Phỏng Xe 2D (Tab 2 - Cột Trái)
    const simLbl    = document.getElementById('simUgCompLabel');
    const btnOff    = document.getElementById('btnSimUgOff');
    const btnOn     = document.getElementById('btnSimUgOn');
    const simBadge  = document.getElementById('simStatusBadge');
    if (simLbl && btnOff && btnOn) {
      if (ugOn) {
        simLbl.style.color = '#d2a8ff';
        simLbl.innerText   = '🌈 ĐÈN GẦM ĐANG BẬT (22 LED SÁNG)';
        btnOff.style.opacity = '1';
        btnOff.style.boxShadow = '0 0 10px rgba(218,54,51,0.45)';
        btnOn.style.opacity  = '0.45';
        btnOn.style.boxShadow = 'none';
        if (simBadge) { simBadge.innerText = '30 PIXELS LIVE'; simBadge.style.color = '#3fb950'; }
      } else {
        simLbl.style.color = '#3fb950';
        simLbl.innerText   = '🏁 CHẾ ĐỘ THI ĐẤU: ĐÃ TẮT ĐÈN GẦM';
        btnOff.style.opacity = '0.45';
        btnOff.style.boxShadow = 'none';
        btnOn.style.opacity  = '1';
        btnOn.style.boxShadow = '0 0 10px rgba(35,134,54,0.5)';
        if (simBadge) { simBadge.innerText = 'THI ĐẤU (TẮT GẦM)'; simBadge.style.color = '#ffd33d'; }
      }
    }

    // 3. Cập nhật Khung Kho 16 Hiệu Ứng Đèn Gầm (Tab 2 - Cột Phải)
    const compBox   = document.getElementById('ugCompetitionBox');
    const compTitle = document.getElementById('ugCompBoxTitle');
    const panelBtn  = document.getElementById('btnPanelToggleUg');
    const hdrBadge  = document.getElementById('ugHeaderBadge');
    const ugGrid    = document.getElementById('ugCardsGrid');
    if (compBox && compTitle && panelBtn) {
      if (ugOn) {
        compBox.style.background  = '#241016';
        compBox.style.borderColor = '#f8514977';
        compTitle.style.color     = '#ff7b72';
        compTitle.innerText       = '🌈 CÔNG TẮC THI ĐẤU: ĐÈN GẦM ĐANG BẬT SÁNG';
        panelBtn.style.background = 'linear-gradient(135deg,#da3633,#f85149)';
        panelBtn.innerText        = '🚫 TẮT HẲN ĐÈN GẦM (THI ĐẤU)';
        if (hdrBadge) { hdrBadge.innerText = '22 Bóng Gầm Đang Bật'; hdrBadge.style.color = '#3fb950'; }
        if (ugGrid)   { ugGrid.style.opacity = '1'; }
      } else {
        compBox.style.background  = '#0c2418';
        compBox.style.borderColor = '#3fb95099';
        compTitle.style.color     = '#3fb950';
        compTitle.innerText       = '✅ ĐÃ TẮT HẲN 22 BÓNG ĐÈN GẦM (SẴN SÀNG VÀO THI ĐẤU)';
        panelBtn.style.background = 'linear-gradient(135deg,#1f6feb,#58a6ff)';
        panelBtn.innerText        = '🌈 MỞ LẠI ĐÈN GẦM';
        if (hdrBadge) { hdrBadge.innerText = '🚫 ĐANG TẮT ĐÈN GẦM (THI ĐẤU)'; hdrBadge.style.color = '#ff7b72'; }
        if (ugGrid)   { ugGrid.style.opacity = '0.42'; }
      }
    }
  }

  async function setUnderglowCompetitionMode(enableUg) {
    curLedConfig.ug_enabled = !!enableUg;
    refreshUnderglowCompetitionUI();

    const logEl = document.getElementById('ledStatusLog');
    const otaEl = document.getElementById('otaLog');
    const statusTxt = enableUg
      ? '🌈 Đang BẬT lại 2 Cụm Đèn Gầm (22 LED) & lưu vào bộ nhớ NVS trên xe...'
      : '🏁 Đang TẮT HẲN 2 Cụm Đèn Gầm (Chế độ Thi Đấu) & khóa lưu vào bộ nhớ NVS trên xe...';
    if (logEl) { logEl.innerText = statusTxt; logEl.style.color = enableUg ? '#58a6ff' : '#3fb950'; }
    if (otaEl) { otaEl.innerText = statusTxt; }

    try {
      const res = await fetch('/api/xedua/led', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(curLedConfig) // live = false -> Lưu thẳng vào NVS trên xe!
      });
      const data = await res.json();
      const doneMsg = (enableUg ? '🌈 ĐÃ BẬT LẠI ĐÈN GẦM: ' : '🏁 CHẾ ĐỘ THI ĐẤU (ĐÃ TẮT ĐÈN GẦM): ') + data.message;
      if (logEl) logEl.innerText = doneMsg;
      if (otaEl) otaEl.innerText = doneMsg;
    } catch (e) {
      if (logEl) logEl.innerText = 'Lỗi đồng bộ trạng thái đèn gầm: ' + e;
    }
  }

  function initLedUI() {
    initColorCanvases();
    fetch('/api/xedua/led')
      .then(r => r.json())
      .then(data => {
        curLedConfig = Object.assign(curLedConfig, data);
        document.getElementById('dotTarget-left').style.background  = curLedConfig.left_color;
        document.getElementById('dotTarget-right').style.background = curLedConfig.right_color;
        document.getElementById('dotTarget-drl').style.background   = curLedConfig.drl_color;
        document.getElementById('dotTarget-ug1').style.background   = curLedConfig.ug_color1;
        document.getElementById('dotTarget-ug2').style.background   = curLedConfig.ug_color2;

        document.getElementById('chkSyncSides').checked  = !!curLedConfig.sync_sides;
        document.getElementById('chkDrlEnabled').checked = curLedConfig.drl_enabled !== false;
        const chkAlways = document.getElementById('chkTurnAlwaysFx');
        if (chkAlways) chkAlways.checked = !!curLedConfig.turn_always_fx;
        const turnBadge = document.getElementById('turnPreviewBadge');
        if (turnBadge) {
          turnBadge.innerText = curLedConfig.turn_always_fx ? '🔥 ĐANG CHẠY LIÊN TỤC 4 CỤM GÓC!' : '⚡ Bấm chọn hiệu ứng ➜ Xe chớp thử ngay!';
          turnBadge.style.color = curLedConfig.turn_always_fx ? '#ff9900' : '#3fb950';
        }
        const chkSwap = document.getElementById('chkSwapTurnDir');
        if (chkSwap) chkSwap.checked = !!curLedConfig.swap_turn_dir;
        document.getElementById('chkUgEnabled').checked  = curLedConfig.ug_enabled !== false;
        document.getElementById('chkUgRevLeft').checked  = !!curLedConfig.ug_rev_left;
        const chkIntro = document.getElementById('chkIntroEnabled');
        if (chkIntro) chkIntro.checked = curLedConfig.intro_enabled !== false;

        document.getElementById('sLedBr').value = curLedConfig.brightness || 90;
        document.getElementById('lLedBr').innerText = (curLedConfig.brightness || 90) + '%';
        document.getElementById('sLedSpd').value = curLedConfig.speed_ms || 280;
        document.getElementById('lLedSpd').innerText = (curLedConfig.speed_ms || 280) + ' ms';

        document.getElementById('sUgSpd').value = curLedConfig.ug_speed_ms || 240;
        document.getElementById('lUgSpd').innerText = (curLedConfig.ug_speed_ms || 240) + ' ms';
        document.getElementById('sUgBr').value = curLedConfig.ug_brightness || 85;
        document.getElementById('lUgBr').innerText = (curLedConfig.ug_brightness || 85) + '%';

        selectColorTarget('left');
        setEffectMode(curLedConfig.mode || 'audi');
        setUgEffectMode(curLedConfig.ug_mode || 'neon_cyber');
        document.querySelectorAll('.mode-card.intro-card').forEach(c => c.classList.remove('active'));
        const introTarget = document.getElementById('introCard-' + (curLedConfig.intro_mode || 'audi_rs'));
        if (introTarget) introTarget.classList.add('active');
        refreshUnderglowCompetitionUI();
        startLedSimulator();
      })
      .catch(() => { refreshUnderglowCompetitionUI(); startLedSimulator(); });
  }

  // =========================================================================
  // BỘ MÔ PHỎNG 32 BÓNG LED TRÊN XE 2D (KHỚP 1:1 THUẬT TOÁN TRÊN ESP32-S3)
  // =========================================================================
  function startLedSimulator() {
    if (simTimer) clearInterval(simTimer);
    simTimer = setInterval(renderSimFrame32, 45);
  }

  function setDomPixel(idx, hexCol) {
    const el = document.getElementById('px' + idx);
    if (!el) return;
    if (!hexCol || hexCol === '#000000') {
      el.style.background = '#151d2c';
      el.style.borderColor = '#344663';
      el.style.boxShadow = 'none';
    } else {
      el.style.background = hexCol;
      el.style.borderColor = '#ffffff';
      el.style.boxShadow = `0 0 10px ${hexCol}, 0 0 18px ${hexCol}`;
    }
  }

  function evalTurnClusterSide(now, baseCol, drlCol, mode, spd) {
    let f0 = '#000000', f1 = '#000000', r0 = '#000000', r1 = '#000000';
    spd = Math.max(80, spd || 280);

    if (mode === 'audi') {
      const cycle = spd * 2;
      const step = Math.floor((now % cycle) * 4 / cycle);
      if (step === 0) { f0 = r0 = baseCol; }
      else if (step === 1 || step === 2) { f0 = f1 = r0 = r1 = baseCol; }
    } else if (mode === 'standard' || mode === 'blink') {
      if ((now % (spd * 2)) < spd) f0 = f1 = r0 = r1 = baseCol;
    } else if (mode === 'strobe_f1' || mode === 'strobe') {
      const t = now % (spd * 2);
      const slice = Math.max(35, (spd * 2) / 8);
      const slot = Math.floor(t / slice);
      if (slot === 0 || slot === 2 || slot === 4) f0 = f1 = r0 = r1 = baseCol;
    } else if (mode === 'pingpong') {
      if ((now % (spd * 2)) < spd) {
        f0 = r0 = baseCol; f1 = r1 = scaleHex(baseCol, 45);
      } else {
        f0 = r0 = scaleHex(baseCol, 45); f1 = r1 = baseCol;
      }
    } else if (mode === 'front_rear') {
      const cycle = spd * 2;
      const step = Math.floor((now % cycle) * 4 / cycle);
      if (step === 0) f0 = baseCol;
      else if (step === 1) { f0 = f1 = baseCol; r0 = scaleHex(baseCol, 150); }
      else if (step === 2) { f1 = scaleHex(baseCol, 130); r0 = r1 = baseCol; }
      else r1 = scaleHex(baseCol, 170);
    } else if (mode === 'pulse') {
      const period = spd * 3;
      const phase = ((now % period) / period) * Math.PI * 2;
      const bri = Math.round((Math.sin(phase) * 0.5 + 0.5) * 240 + 15);
      f0 = f1 = r0 = r1 = scaleHex(baseCol, bri);
    } else if (mode === 'heartbeat') {
      const t = ((now % (spd * 3)) * 1000) / (spd * 3);
      let bri = 20;
      if (t < 120) bri = 255;
      else if (t < 220) bri = 45;
      else if (t < 360) bri = 255;
      else if (t < 550) bri = Math.round(255 - (t - 360) * 235 / 190);
      f0 = f1 = r0 = r1 = scaleHex(baseCol, bri);
    } else if (mode === 'sparkle') {
      const cBase = scaleHex(baseCol, 165);
      f0 = f1 = r0 = r1 = cBase;
      const sIdx = Math.floor(now / 55) % 4;
      if (sIdx === 0) f0 = '#FFFFFF';
      else if (sIdx === 1) f1 = '#FFFFFF';
      else if (sIdx === 2) r0 = '#FFFFFF';
      else r1 = '#FFFFFF';
    } else if (mode === 'police_turn') {
      const red = '#FF0A18', blue = '#0078FF';
      const sideA = (Math.floor(now / (spd / 2 + 30)) % 2) === 0;
      const fast  = (Math.floor(now / 45) % 2) === 0;
      if (sideA) {
        f0 = f1 = fast ? red : '#000000';
        r0 = r1 = fast ? '#000000' : blue;
      } else {
        f0 = f1 = fast ? blue : '#000000';
        r0 = r1 = fast ? '#000000' : red;
      }
    } else if (mode === 'laser_shot') {
      const cycle = spd * 2;
      const pos = ((now % cycle) * 255) / cycle;
      const b0 = (pos < 128) ? Math.round(255 - pos * 2) : 0;
      const b1 = (pos >= 64 && pos < 220) ? Math.round(Math.max(0, 255 - Math.abs(pos - 135) * 2)) : 0;
      f0 = r0 = scaleHex(baseCol, b0);
      f1 = r1 = scaleHex(baseCol, b1);
    } else if (mode === 'rainbow_turn' || mode === 'rainbow') {
      const h = Math.floor((now * 360) / (spd * 3)) % 360;
      f0 = hsvToHex(h, 100, 100);
      f1 = hsvToHex((h + 45) % 360, 100, 100);
      r0 = hsvToHex((h + 90) % 360, 100, 100);
      r1 = hsvToHex((h + 135) % 360, 100, 100);
    } else if (mode === 'plasma_dual') {
      const period = spd * 3;
      const w0 = Math.round((Math.sin(((now % period) / period) * Math.PI * 2) * 0.5 + 0.5) * 255);
      f0 = r0 = blendHex(baseCol, drlCol, w0);
      f1 = r1 = blendHex(baseCol, drlCol, 255 - w0);
    }
    return [f0, f1, r0, r1];
  }

  const CORNER_RING8 = [1, 0, 2, 3, 5, 4, 6, 7];
  const FRONT_BAR4   = [3, 2, 0, 1];
  const REAR_BAR4    = [5, 4, 6, 7];

  function simCornerHaloComet(pixels, headPos, tailCol, tailLen, dualOpposite, bgBri) {
    for (let k = 0; k < 8; k++) {
      let bestBri = bgBri, bestWMix = 0;
      for (let pass = 0; pass < (dualOpposite ? 2 : 1); pass++) {
        const hp = ((headPos + (pass === 1 ? 4.0 : 0.0)) % 8 + 8) % 8;
        const behind = ((hp - k) % 8 + 8) % 8;
        const ahead  = 8.0 - behind;
        let bri = 0, wMix = 0;
        if (ahead < 0.85) {
          bri  = Math.round((1.0 - ahead / 0.85) * 230);
          wMix = Math.round((1.0 - ahead / 0.85) * 200);
        } else if (behind <= tailLen) {
          const norm = 1.0 - (behind / tailLen);
          bri = Math.round(norm * norm * 255);
          if (behind < 0.75) wMix = Math.round((1.0 - behind / 0.75) * 235);
        }
        if (bri > bestBri) bestBri = bri;
        if (wMix > bestWMix) bestWMix = wMix;
      }
      pixels[CORNER_RING8[k]] = scaleHex(blendHex(tailCol, '#FFFFFF', bestWMix), bestBri);
    }
  }

  function simCornerBarScan4(pixels, posFront, posRear, fCol, rCol, whiteCore) {
    for (let k = 0; k < 4; k++) {
      const df = Math.abs(k - posFront);
      const bf = (df < 1.65) ? Math.round((1.0 - df / 1.65) * 255) : 22;
      const cf = (whiteCore && df < 0.55) ? blendHex(fCol, '#FFFFFF', Math.round((1.0 - df / 0.55) * 215)) : fCol;
      pixels[FRONT_BAR4[k]] = scaleHex(cf, bf);

      const dr = Math.abs(k - posRear);
      const br = (dr < 1.65) ? Math.round((1.0 - dr / 1.65) * 255) : 22;
      const cr = (whiteCore && dr < 0.55) ? blendHex(rCol, '#FFFFFF', Math.round((1.0 - dr / 0.55) * 215)) : rCol;
      pixels[REAR_BAR4[k]] = scaleHex(cr, br);
    }
  }

  function simCornerAudiWipe(pixels, subMs, cycleMs, rightCol, leftCol, bgCol) {
    const p = (subMs % cycleMs) / cycleMs;
    let bIn = 0, bOut = 0, wIn = 0, wOut = 0;
    if (p < 0.26) {
      const t = p / 0.26;
      bIn = Math.round(t * 255);
      wIn = Math.round(Math.sin(t * Math.PI) * 185);
    } else if (p < 0.58) {
      const t = (p - 0.26) / 0.32;
      bIn = 255;
      bOut = Math.round(t * 255);
      wOut = Math.round(Math.sin(t * Math.PI) * 225);
    } else if (p < 0.85) {
      const t = (p - 0.58) / 0.27;
      bIn  = Math.round(Math.max(0, 1.0 - t * 1.55) * 255);
      bOut = Math.round((1.0 - t * t) * 255);
    }
    const rIn  = (bIn > 0)  ? scaleHex(blendHex(rightCol, '#FFFFFF', wIn),  bIn)  : bgCol;
    const rOut = (bOut > 0) ? scaleHex(blendHex(rightCol, '#FFFFFF', wOut), bOut) : bgCol;
    const lIn  = (bIn > 0)  ? scaleHex(blendHex(leftCol,  '#FFFFFF', wIn),  bIn)  : bgCol;
    const lOut = (bOut > 0) ? scaleHex(blendHex(leftCol,  '#FFFFFF', wOut), bOut) : bgCol;
    pixels[0] = pixels[6] = rIn;  pixels[1] = pixels[7] = rOut;
    pixels[2] = pixels[4] = lIn;  pixels[3] = pixels[5] = lOut;
  }

  function renderSimIntro32(elapsed, pixels) {
    const mode = curLedConfig.intro_mode || 'audi_rs';
    const c1 = curLedConfig.ug_color1 || '#00E5FF';
    const c2 = curLedConfig.ug_color2 || '#9D00FF';
    const cTurnL = curLedConfig.left_color || '#FFAA00';
    const cTurnR = curLedConfig.right_color || '#FFAA00';
    const cDrl = curLedConfig.drl_color || '#00E5FF';
    const maxIdx = UG_LEN - 1; // 10
    const centerIdx = maxIdx * 0.5; // 5.0
    const setUgPair = (i, col) => {
      if (curLedConfig.ug_enabled === false) return;
      if (i < 0 || i >= UG_LEN) return;
      pixels[IDX_R_UG + i] = col;
      const li = curLedConfig.ug_rev_left ? (maxIdx - i) : i;
      pixels[IDX_L_UG + li] = col;
    };

    if (mode === 'audi_rs') {
      if (elapsed < 700) {
        if (elapsed < 500) {
          simCornerHaloComet(pixels, (elapsed / 500.0) * 16.0, cDrl, 2.6, true, 18);
        } else {
          const outerHit = (elapsed >= 595);
          const cIn  = outerHit ? cDrl : '#FFFFFF';
          const cOut = outerHit ? '#FFFFFF' : scaleHex(cDrl, 45);
          pixels[0] = pixels[2] = pixels[4] = pixels[6] = cIn;
          pixels[1] = pixels[3] = pixels[5] = pixels[7] = cOut;
        }
        const lead = Math.floor(elapsed * 5 / 700);
        for (let i = 0; i <= lead && i < UG_LEN; i++) setUgPair(i, '#FFFFFF');
      } else if (elapsed < 1800) {
        const sub = elapsed - 700;
        const prog = sub / 1100.0;
        const scan4 = (Math.sin(prog * Math.PI * 4) * 0.5 + 0.5) * 3.0;
        const fBarCol = (prog < 0.5) ? cDrl : blendHex(cTurnL, cDrl, Math.round((prog - 0.5) * 510));
        const rBarCol = (prog < 0.5) ? blendHex(c2, cTurnL, Math.round(prog * 510)) : c1;
        simCornerBarScan4(pixels, scan4, 3.0 - scan4, fBarCol, rBarCol, true);
        if (prog > 0.44 && prog < 0.56) { pixels[5] = pixels[7] = '#FFFFFF'; }
        else if (prog > 0.90) { pixels[1] = pixels[3] = '#FFFFFF'; }

        const pos = Math.round(((prog < 0.5) ? (prog * 2 * maxIdx) : ((1 - (prog - 0.5) * 2) * maxIdx)) * 10);
        for (let i = 0; i < UG_LEN; i++) {
          const d = Math.abs(i * 10 - pos);
          const b = (d < 36) ? Math.round((1 - d / 36) * 255) : 25;
          setUgPair(i, scaleHex(blendHex(c1, c2, Math.round(i * 255 / maxIdx)), b));
        }
      } else if (elapsed < 2800) {
        const sub = elapsed - 1800;
        const reach = Math.floor((sub * 6) / 1000);
        for (let i = 0; i < UG_LEN; i++) {
          const distCenter = Math.abs(i - centerIdx);
          if (distCenter <= reach) {
            setUgPair(i, blendHex(c1, c2, Math.round(i * 255 / maxIdx)));
          }
        }
        simCornerAudiWipe(pixels, sub, 333, cTurnR, cTurnL, scaleHex(cDrl, 30));
      } else {
        const sub = elapsed - 2800;
        const fade = Math.min(255, Math.max(55, Math.round(sub * 255 / 800)));
        for (let k = 0; k < 8; k++) {
          const wave = Math.round((Math.sin(sub * 0.012 + k * 0.8) * 0.25 + 0.75) * fade);
          pixels[CORNER_RING8[k]] = scaleHex(blendHex(cTurnL, cDrl, fade), wave);
        }
        if (sub < 660) {
          const spkA = Math.floor(elapsed / 42) % 8;
          pixels[CORNER_RING8[spkA]] = '#FFFFFF';
          pixels[CORNER_RING8[(spkA + 4) % 8]] = blendHex(cDrl, '#FFFFFF', 190);
        }
        for (let i = 0; i < UG_LEN; i++) setUgPair(i, scaleHex(blendHex(c1, c2, Math.round(i * 255 / maxIdx)), fade));
        const spk = Math.floor(elapsed / 45) % UG_LEN;
        setUgPair(spk, '#FFFFFF');
      }
    } else if (mode === 'cyber_ignite') {
      if (elapsed < 800) {
        const tick = Math.floor(elapsed / 42);
        for (let k = 0; k < 8; k++) {
          const h = (k * 7 + tick * 13) % 9;
          pixels[CORNER_RING8[k]] = (h === 0) ? '#FFFFFF' : ((h === 1 || h === 4) ? c1 : ((h === 2 || h === 6) ? c2 : '#000000'));
        }
        const gIdx = (tick * 5) % UG_LEN;
        setUgPair(gIdx, c1);
        setUgPair((gIdx + 5) % UG_LEN, c2);
      } else if (elapsed < 2400) {
        const sub = elapsed - 800;
        const norm = sub / 1600.0;
        const accelSpin = (norm * norm * 3.2 + norm * 0.8) * 8.0;
        simCornerHaloComet(pixels, accelSpin, blendHex(c1, c2, Math.round(norm * 255)), 2.8, true, 22);
        const filled = Math.floor((sub * (UG_LEN + 1)) / 1600);
        for (let i = 0; i < UG_LEN; i++) {
          if (i < filled) setUgPair(i, blendHex(c1, c2, Math.round(i * 255 / maxIdx)));
          else if (i === filled) setUgPair(i, '#FFFFFF');
        }
      } else {
        const sub = elapsed - 2400;
        const baseH = Math.floor(elapsed / 2) % 360;
        if (sub < 220) {
          const alt = (Math.floor(sub / 35) % 2) === 0;
          for (let b = 0; b < 8; b += 2) {
            pixels[b] = alt ? '#FFFFFF' : c1;
            pixels[b + 1] = alt ? c2 : '#FFFFFF';
          }
          for (let i = 0; i < UG_LEN; i++) setUgPair(i, '#FFFFFF');
        } else {
          for (let k = 0; k < 8; k++) pixels[CORNER_RING8[k]] = hsvToHex((baseH + k * 45) % 360, 100, 100);
          for (let i = 0; i < UG_LEN; i++) {
            const h = (Math.round(i * 360 / UG_LEN) + baseH) % 360;
            setUgPair(i, hsvToHex(h, 100, 100));
          }
        }
      }
    } else if (mode === 'lambo_v12') {
      const red = '#FF0A00', org = '#FF6E00', gold = '#FFE600';
      if (elapsed < 1000) {
        const t = elapsed % 500;
        const bIn  = (t < 115 || (t >= 180 && t < 320)) ? 255 : 22;
        const bOut = (t >= 195 && t < 340) ? 255 : ((t < 115) ? 65 : 15);
        for (let b = 0; b < 8; b += 2) {
          pixels[b] = scaleHex(red, bIn);
          pixels[b + 1] = scaleHex((t >= 195 && t < 260) ? org : red, bOut);
        }
        const c = scaleHex(red, bIn);
        setUgPair(maxIdx - 1, c); setUgPair(maxIdx, c);
      } else if (elapsed < 2300) {
        const sub = elapsed - 1000;
        const frontReach = maxIdx - Math.floor((sub * UG_LEN) / 1300);
        if (frontReach <= 2) {
          const outerHit = (frontReach <= 0);
          pixels[0] = pixels[2] = outerHit ? gold : '#FFFFFF';
          pixels[1] = pixels[3] = outerHit ? '#FFFFFF' : org;
        } else {
          simCornerAudiWipe(pixels, sub, 420, org, org, scaleHex(red, 35));
        }
        for (let p = 4; p <= 7; p++) {
          const pop = Math.floor(sub / 38 + p * 3) % 4;
          pixels[p] = (pop === 0) ? '#FFFFFF' : ((pop === 1) ? gold : red);
        }
        for (let i = maxIdx; i >= Math.max(0, frontReach); i--) {
          if (i === frontReach) setUgPair(i, '#FFFFFF');
          else if (i <= frontReach + 2) setUgPair(i, gold);
          else setUgPair(i, blendHex(org, red, Math.round(i * 255 / maxIdx)));
        }
      } else {
        for (let p = 0; p < 8; p++) {
          const flk = 135 + ((elapsed * (p + 3) * 29 + p * 61) % 120);
          const baseF = (p >= 4) ? blendHex(red, gold, flk) : blendHex(org, gold, flk);
          pixels[p] = (p >= 4 && ((Math.floor(elapsed / 45) + p) % 7 === 0)) ? '#FFFFFF' : scaleHex(baseF, flk);
        }
        for (let i = 0; i < UG_LEN; i++) {
          const wave = Math.round((Math.sin(elapsed / 55 + i * 0.7) * 0.5 + 0.5) * 215 + 40);
          setUgPair(i, scaleHex(blendHex(gold, red, Math.round(i * 255 / maxIdx)), wave));
        }
      }
    } else if (mode === 'knight_scanner') {
      if (elapsed < 1200) {
        simCornerHaloComet(pixels, (elapsed / 1200.0) * 16.0, c1, 2.8, false, 18);
        const ugPos = Math.floor(elapsed * UG_LEN / 1200);
        for (let i = 0; i < UG_LEN; i++) {
          if (Math.abs(i - ugPos) <= 1) setUgPair(i, c1);
        }
      } else {
        const sub = elapsed - 1200;
        const pBar = (sub % 800) / 800.0;
        const barPosF = (pBar < 0.5) ? (pBar * 6.0) : ((1.0 - (pBar - 0.5) * 2.0) * 3.0);
        simCornerBarScan4(pixels, barPosF, 3.0 - barPosF, c1, c2, true);

        const cycle = sub % 1200;
        const pos1 = Math.round(((cycle < 600) ? (cycle * maxIdx / 600) : ((1200 - cycle) * maxIdx / 600)) * 10);
        const pos2 = maxIdx * 10 - pos1;
        for (let i = 0; i < UG_LEN; i++) {
          const d1 = Math.abs(i * 10 - pos1);
          const d2 = Math.abs(i * 10 - pos2);
          const b1 = (d1 < 32) ? (255 - d1 * 7) : 15;
          const b2 = (d2 < 32) ? (255 - d2 * 7) : 15;
          if (curLedConfig.ug_enabled !== false) {
            pixels[IDX_R_UG + i] = scaleHex(c1, b1);
            const li = curLedConfig.ug_rev_left ? (maxIdx - i) : i;
            pixels[IDX_L_UG + li] = scaleHex(c2, b2);
          }
        }
      }
    } else if (mode === 'f1_countdown') {
      const red = '#FF0010', grn = '#00FF46', yel = '#FFC800';
      if (elapsed < 2400) {
        const stage = Math.floor(elapsed / 480) + 1;
        const stSub = elapsed % 480;
        const pulseHit = (stSub < 140);
        if (stage === 1) {
          pixels[0] = pixels[2] = pulseHit ? '#FFFFFF' : grn;
        } else if (stage === 2) {
          pixels[0] = pixels[2] = yel;
          pixels[1] = pixels[3] = pulseHit ? '#FFFFFF' : yel;
        } else if (stage === 3) {
          pixels[0] = pixels[1] = pixels[2] = pixels[3] = red;
          pixels[4] = pixels[6] = pulseHit ? '#FFFFFF' : yel;
        } else if (stage === 4) {
          pixels[0] = pixels[1] = pixels[2] = pixels[3] = pixels[4] = pixels[6] = red;
          pixels[5] = pixels[7] = pulseHit ? '#FFFFFF' : red;
        } else {
          const rev = (Math.floor(stSub / 45) % 2) === 0;
          for (let b = 0; b < 8; b += 2) {
            pixels[b] = red;
            pixels[b + 1] = rev ? red : blendHex(red, yel, 160);
          }
        }
        if (stage >= 1) { setUgPair(0, red); setUgPair(1, red); }
        if (stage >= 2) { setUgPair(2, red); setUgPair(3, red); }
        if (stage >= 3) { setUgPair(4, red); setUgPair(5, red); setUgPair(6, red); }
        if (stage >= 4) { setUgPair(7, red); setUgPair(8, red); }
        if (stage >= 5) { setUgPair(9, red); setUgPair(10, red); }
      } else if (elapsed < 2680) {
        // Lights Out!
      } else {
        const strobe = (Math.floor((elapsed - 2680) / 55) % 2) === 0;
        for (let b = 0; b < 8; b += 2) {
          pixels[b]     = strobe ? grn : '#FFFFFF';
          pixels[b + 1] = strobe ? '#FFFFFF' : grn;
        }
        for (let i = 0; i < UG_LEN; i++) setUgPair(i, (i % 2 === 0) ? grn : (strobe ? grn : '#FFFFFF'));
      }
    } else if (mode === 'galaxy_supernova') {
      if (elapsed < 1500) {
        const norm = elapsed / 1500.0;
        simCornerHaloComet(pixels, 8.0 - norm * norm * 16.0, blendHex(c1, c2, Math.round(norm * 255)), 2.5, true, 16);
        const radius = (1.0 - norm) * 5.5;
        for (let i = 0; i < UG_LEN; i++) {
          const diff = Math.abs(Math.abs(i - centerIdx) - radius);
          const bri = (diff < 1.8) ? Math.round((1.0 - diff / 1.8) * 255) : 15;
          setUgPair(i, scaleHex(c1, bri));
        }
      } else if (elapsed < 2000) {
        const vib = (Math.floor(elapsed / 35) % 2) === 0;
        for (let b = 0; b < 8; b += 2) {
          const diag = (b === 0 || b === 4) ? vib : !vib;
          pixels[b] = diag ? '#FFFFFF' : c1;
          pixels[b + 1] = scaleHex(c2, 30);
        }
        setUgPair(4, vib ? '#FFFFFF' : c1);
        setUgPair(5, vib ? '#FFFFFF' : c2);
        setUgPair(6, vib ? '#FFFFFF' : c1);
      } else {
        const sub = elapsed - 2000;
        const rad = (sub / 600.0) * 6.5;
        const baseH = Math.floor(elapsed / 2.5) % 360;
        for (let i = 0; i < UG_LEN; i++) {
          if (Math.abs(i - centerIdx) <= rad) setUgPair(i, hsvToHex((baseH + Math.round(i * 360 / UG_LEN)) % 360, 100, 100));
        }
        if (sub < 220) {
          const hitOuter = (sub >= 100);
          for (let b = 0; b < 8; b += 2) {
            pixels[b] = hitOuter ? c1 : '#FFFFFF';
            pixels[b + 1] = hitOuter ? '#FFFFFF' : '#000000';
          }
        } else {
          const star = Math.floor(elapsed / 50) % 8;
          for (let k = 0; k < 8; k++) {
            pixels[CORNER_RING8[k]] = (k === star) ? '#FFFFFF' : hsvToHex((baseH + k * 45) % 360, 100, 100);
          }
        }
      }
    } else if (mode === 'police_vip') {
      const red = '#FF0014', blue = '#005AFF';
      const phase = Math.floor(elapsed / 180) % 4;
      const fast = (Math.floor(elapsed / 40) % 2) === 0;
      const cA = fast ? red : '#FFFFFF';
      const cB = fast ? blue : '#000000';
      if (phase === 0) {
        pixels[1] = pixels[5] = fast ? red : '#000000';  pixels[0] = pixels[4] = fast ? '#000000' : '#FFFFFF';
        pixels[3] = pixels[7] = blue;                    pixels[2] = pixels[6] = scaleHex(blue, 85);
      } else if (phase === 1) {
        pixels[1] = pixels[5] = red;                     pixels[0] = pixels[4] = scaleHex(red, 85);
        pixels[3] = pixels[7] = fast ? blue : '#000000'; pixels[2] = pixels[6] = fast ? '#000000' : '#FFFFFF';
      } else if (phase === 2) {
        const scan = ((elapsed % 180) / 180.0) * 3.0;
        simCornerBarScan4(pixels, scan, 3.0 - scan, red, blue, true);
      } else {
        const scan = ((elapsed % 180) / 180.0) * 3.0;
        simCornerBarScan4(pixels, 3.0 - scan, scan, blue, red, true);
      }
      if (curLedConfig.ug_enabled !== false) {
        for (let i = 0; i < UG_LEN; i++) {
          if (phase % 2 === 0) {
            pixels[IDX_R_UG + i] = (i <= 5) ? cA : cB;
            pixels[IDX_L_UG + i] = (i <= 5) ? cB : cA;
          } else {
            pixels[IDX_R_UG + i] = (i <= 5) ? cB : cA;
            pixels[IDX_L_UG + i] = (i <= 5) ? cA : cB;
          }
        }
      }
    } else if (mode === 'royal_gold') {
      const gold = '#FFAF00', pearl = '#FFF5D7';
      const prog = elapsed / 3600.0;
      const spread = prog * 7.5;
      const env = Math.round(Math.sin(prog * Math.PI) * 255);
      for (let k = 0; k < 8; k++) {
        const silk = Math.sin(elapsed * 0.0065 - k * 0.785) * 0.5 + 0.5;
        const c = blendHex(gold, pearl, Math.round(silk * 235));
        const pixBri = Math.min(255, Math.max(20, Math.round(env * (0.55 + 0.45 * silk))));
        pixels[CORNER_RING8[k]] = scaleHex(c, pixBri);
      }
      pixels[CORNER_RING8[Math.floor(elapsed / 85) % 8]] = scaleHex('#FFFFFF', env);
      for (let i = 0; i < UG_LEN; i++) {
        const dist = Math.abs(i - centerIdx);
        if (dist <= spread) {
          const b = Math.min(255, Math.max(30, Math.round((1.0 - dist / (spread + 0.5)) * 255)));
          setUgPair(i, scaleHex(blendHex(pearl, gold, Math.round(dist * 48)), b));
        }
      }
    }
  }

  function renderSimFrame32() {
    const now = Date.now();
    const pixels = new Array(NUM_LEDS_TOTAL).fill('#000000');

    if (simIntroPlaying) {
      const elapsed = now - simIntroStartMs;
      if (elapsed <= 3600) {
        renderSimIntro32(elapsed, pixels);
        for (let i = 0; i < NUM_LEDS_TOTAL; i++) setDomPixel(i, pixels[i]);
        return;
      } else {
        simIntroPlaying = false;
      }
    }

    const doRight    = (simActiveState === 'right' || simActiveState === 'hazard');
    const doLeft     = (simActiveState === 'left'  || simActiveState === 'hazard');
    const doTurnShow = !!curLedConfig.turn_always_fx && (simActiveState !== 'off_all');
    const doDrl      = (curLedConfig.drl_enabled !== false || simActiveState === 'drl') && (simActiveState !== 'off_all');
    const doUg       = (curLedConfig.ug_enabled !== false) && (curLedConfig.ug_mode !== 'off') && (simActiveState !== 'off_all');

    // 1..3. 4 cụm góc xe (LED 0..7): Hỗ trợ cả Chế độ Show Liên Tục lẫn Chế độ Xi Nhan Khi Rẽ
    if (doTurnShow && !doRight && !doLeft) {
      const [rf0, rf1, rr0, rr1] = evalTurnClusterSide(now, curLedConfig.right_color, curLedConfig.drl_color, curLedConfig.mode, curLedConfig.speed_ms);
      pixels[0] = rf0; pixels[1] = rf1; pixels[6] = rr0; pixels[7] = rr1;
      const [lf0, lf1, lr0, lr1] = evalTurnClusterSide(now, curLedConfig.left_color, curLedConfig.drl_color, curLedConfig.mode, curLedConfig.speed_ms);
      pixels[2] = lf0; pixels[3] = lf1; pixels[4] = lr0; pixels[5] = lr1;
    } else {
      if (doDrl) {
        const drlScaled = scaleHex(curLedConfig.drl_color, doTurnShow ? 65 : 175);
        if (!doRight) {
          pixels[0] = pixels[1] = pixels[6] = pixels[7] = drlScaled;
        }
        if (!doLeft) {
          pixels[2] = pixels[3] = pixels[4] = pixels[5] = drlScaled;
        }
      }
      if (doRight) {
        const [f0, f1, r0, r1] = evalTurnClusterSide(now, curLedConfig.right_color, curLedConfig.drl_color, curLedConfig.mode, curLedConfig.speed_ms);
        pixels[0] = f0; pixels[1] = f1;
        pixels[6] = r0; pixels[7] = r1;
      }
      if (doLeft) {
        const [f0, f1, r0, r1] = evalTurnClusterSide(now, curLedConfig.left_color, curLedConfig.drl_color, curLedConfig.mode, curLedConfig.speed_ms);
        pixels[2] = f0; pixels[3] = f1;
        pixels[4] = r0; pixels[5] = r1;
      }
    }

    // 4. Hiệu ứng 2 Cụm Đèn Gầm Độc Lập: Cụm 5 (Gầm Phải: 8..18) & Cụm 6 (Gầm Trái: 19..29)
    if (doUg) {
      const ugMode = curLedConfig.ug_mode || 'neon_cyber';
      const spd = Math.max(60, curLedConfig.ug_speed_ms || 240);
      const ugBri = Math.round(((curLedConfig.ug_brightness || 85) * 255) / 100);
      const col1 = curLedConfig.ug_color1 || '#00E5FF';
      const col2 = curLedConfig.ug_color2 || '#9D00FF';
      const maxIdx = UG_LEN - 1; // 10
      const centerIdx = maxIdx * 0.5; // 5.0

      for (let i = 0; i < UG_LEN; i++) {
        let cR = '#000000', cL = '#000000';
        if (ugMode === 'neon_cyber') {
          const h = (Math.floor(now / (spd / 12)) + Math.round(i * 360 / UG_LEN)) % 360;
          cR = cL = hsvToHex(h, 100, 100);
        } else if (ugMode === 'knight_rider') {
          const cycle = spd * 4;
          const prog = (now % cycle) / cycle;
          const pos = (prog < 0.5) ? (prog * 2 * maxIdx) : ((1 - (prog - 0.5) * 2) * maxIdx);
          const dist = Math.abs(i - pos);
          const inten = (dist < 3.5) ? Math.round((1 - dist / 3.5) * 255) : 18;
          cR = cL = scaleHex(blendHex(col2, col1, inten), inten);
        } else if (ugMode === 'meteor_rain') {
          const head = Math.floor(now / (spd / 3 + 15)) % (UG_LEN + 6);
          const d = head - i;
          if (d === 0) cR = cL = '#FFFFFF';
          else if (d > 0 && d <= 6) {
            const fade = 255 - d * 38;
            cR = cL = scaleHex(blendHex(col1, col2, d * 40), fade);
          }
        } else if (ugMode === 'dual_flow') {
          const period = spd * 5;
          const phase = ((now % period) / period) * Math.PI * 2;
          const w = Math.round((Math.sin(phase - i * 0.55) * 0.5 + 0.5) * 255);
          cR = cL = blendHex(col1, col2, w);
        } else if (ugMode === 'center_burst') {
          const cycle = spd * 3;
          const rad = ((now % cycle) / cycle) * 6.5;
          const distC = Math.abs(i - centerIdx);
          const diff = Math.abs(distC - rad);
          const bri = (diff < 2.2) ? Math.round((1 - diff / 2.2) * 255) : 25;
          cR = cL = scaleHex(blendHex(col1, col2, Math.round(distC * 50)), bri);
        } else if (ugMode === 'converge_in') {
          const cycle = spd * 3;
          const rad = (1 - (now % cycle) / cycle) * 6.0;
          const distC = Math.abs(i - centerIdx);
          const diff = Math.abs(distC - rad);
          const bri = (diff < 2.2) ? Math.round((1 - diff / 2.2) * 255) : 25;
          cR = cL = scaleHex(blendHex(col2, col1, Math.round(distC * 50)), bri);
        } else if (ugMode === 'nitro_flame') {
          const flk = 150 + ((now * (i + 3) * 17 + i * 73) % 105);
          const base = blendHex(col1, col2, Math.round(i * 255 / maxIdx));
          cR = scaleHex(base, flk);
          cL = scaleHex(base, 255 - Math.floor(flk / 3));
        } else if (ugMode === 'police_pursuit') {
          const red = '#FF0018', blue = '#0066FF', white = '#FFFFFF';
          const ph = Math.floor(now / (spd / 2 + 25)) % 4;
          const str = (Math.floor(now / 40) % 2) === 0;
          const fHalf = (i <= 5);
          if (ph === 0) { cR = fHalf ? (str ? red : '#000000') : blue; cL = fHalf ? blue : (str ? red : '#000000'); }
          else if (ph === 1) { cR = fHalf ? blue : (str ? white : '#000000'); cL = fHalf ? (str ? white : '#000000') : blue; }
          else if (ph === 2) { cR = str ? red : '#000000'; cL = str ? '#000000' : blue; }
          else { cR = str ? '#000000' : red; cL = str ? blue : '#000000'; }
        } else if (ugMode === 'throttle_react') {
          const offset = Math.floor(now / 90) % UG_LEN;
          const pos = (i + UG_LEN - offset) % UG_LEN;
          const bri = (pos < 4) ? (255 - pos * 55) : 40;
          cR = cL = scaleHex(blendHex(col1, col2, 128), bri);
        } else if (ugMode === 'galaxy_twinkle') {
          const bg = scaleHex(col1, 80);
          const s1 = Math.floor(now / (spd / 2 + 20)) % UG_LEN;
          const s2 = (Math.floor(now / (spd / 3 + 30)) * 7 + 3) % UG_LEN;
          cR = (i === s1) ? '#FFFFFF' : ((i === s2) ? col2 : bg);
          cL = ((maxIdx - i) === s1) ? col2 : ((i === s2) ? '#FFFFFF' : bg);
        } else if (ugMode === 'breathing_sync') {
          const period = spd * 6;
          const p = ((now % period) / period) * Math.PI * 2;
          const bri = Math.round((Math.sin(p) * 0.5 + 0.5) * 235 + 20);
          const mix = Math.round((Math.cos(p * 0.5) * 0.5 + 0.5) * 255);
          cR = cL = scaleHex(blendHex(col1, col2, mix), bri);
        } else if (ugMode === 'theater_chase') {
          const shift = Math.floor(now / (spd / 3 + 25)) % 3;
          cR = cL = ((i + shift) % 3 === 0) ? col1 : (((i + shift) % 3 === 1) ? scaleHex(col2, 160) : '#000000');
        } else if (ugMode === 'strobe_matrix') {
          const seg = Math.floor(now / (spd / 3 + 20)) % 3;
          const fl = (Math.floor(now / 40) % 2) === 0;
          const mySeg = Math.floor((i * 3) / UG_LEN);
          cR = cL = (mySeg === seg && fl) ? ((seg % 2 === 0) ? col1 : col2) : scaleHex(col1, 30);
        } else if (ugMode === 'ocean_aurora') {
          const t = now * 0.004 + i * 0.45;
          const mix = Math.round((Math.sin(t) * 0.5 + 0.5) * 255);
          const bri = Math.round((Math.cos(t * 0.7 - i * 0.3) * 0.4 + 0.6) * 255);
          cR = cL = scaleHex(blendHex(col1, col2, mix), bri);
        } else if (ugMode === 'turn_sync_ug') {
          const cycle = spd * 2;
          const step = Math.floor((now % cycle) * (UG_LEN + 2) / cycle);
          cR = doRight ? ((i <= step) ? curLedConfig.right_color : scaleHex(col1, 35)) : col1;
          cL = doLeft  ? ((i <= step) ? curLedConfig.left_color  : scaleHex(col1, 35)) : col1;
        } else {
          cR = cL = blendHex(col1, col2, Math.round(i * 255 / maxIdx));
        }

        pixels[IDX_R_UG + i] = scaleHex(cR, ugBri);
        const leftIdx = curLedConfig.ug_rev_left ? (IDX_L_UG + (maxIdx - i)) : (IDX_L_UG + i);
        pixels[leftIdx] = scaleHex(cL, ugBri);
      }
    }

    for (let k = 0; k < NUM_LEDS_TOTAL; k++) {
      setDomPixel(k, pixels[k]);
    }

    const fxUnderglow = document.getElementById('fxUnderglow');
    if (fxUnderglow) {
      if (doUg) {
        fxUnderglow.style.background = `linear-gradient(180deg, ${curLedConfig.ug_color1}, ${curLedConfig.ug_color2})`;
        fxUnderglow.style.opacity = '0.45';
      } else if (doRight || doLeft) {
        fxUnderglow.style.background = doLeft ? curLedConfig.left_color : curLedConfig.right_color;
        fxUnderglow.style.opacity = '0.28';
      } else {
        fxUnderglow.style.opacity = '0';
      }
    }
  }

  async function saveAndApplyLedConfig() {
    curLedConfig.brightness = parseInt(document.getElementById('sLedBr').value) || 90;
    curLedConfig.speed_ms = parseInt(document.getElementById('sLedSpd').value) || 280;
    curLedConfig.ug_speed_ms = parseInt(document.getElementById('sUgSpd').value) || 240;
    curLedConfig.ug_brightness = parseInt(document.getElementById('sUgBr').value) || 85;

    const logEl = document.getElementById('ledStatusLog');
    logEl.innerText = 'Đang lưu cấu hình 6 cụm LED và truyền xuống xe qua WiFi...';

    try {
      const res = await fetch('/api/xedua/led', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(curLedConfig)
      });
      const data = await res.json();
      logEl.innerText = data.message;
      alert(data.message);
    } catch (e) {
      logEl.innerText = 'Lỗi lưu cấu hình: ' + e;
    }
  }

  function resetLedDefault() {
    if (!confirm('Khôi phục cấu hình 6 cụm LED về mặc định (Xi nhan Hổ Phách Audi + Gầm Cầu Vồng)?')) return;
    curLedConfig = {
      left_color: '#FFAA00',
      right_color: '#FFAA00',
      drl_color: '#00E5FF',
      sync_sides: true,
      mode: 'audi',
      brightness: 90,
      speed_ms: 280,
      drl_enabled: true,
      turn_always_fx: false,
      swap_turn_dir: false,
      ug_color1: '#00E5FF',
      ug_color2: '#9D00FF',
      ug_mode: 'neon_cyber',
      ug_speed_ms: 240,
      ug_brightness: 85,
      ug_enabled: true,
      ug_rev_left: false,
      intro_mode: 'audi_rs',
      intro_enabled: true
    };
    saveAndApplyLedConfig();
    initLedUI();
  }

  initLedUI();

  // =========================================================================
  // LOGIC CŨ CỦA DASHBOARD RACING & HUD
  // =========================================================================
  const canvas = document.getElementById('hud');
  const ctx = canvas.getContext('2d');
  const W = 600, H = 600, CX = 300, CY = 300, R = 285;

  let speedCapHistory = [];
  let isCarRunning = false;
  let topSpeedThisRun = 0.0;

  function drawHorizon(pitch=0, roll=0, yaw=0, flightState=0) {
    ctx.clearRect(0,0,W,H);
    ctx.save();
    ctx.beginPath();
    ctx.arc(CX, CY, R, 0, Math.PI * 2);
    ctx.clip();

    ctx.save();
    ctx.translate(CX, CY);
    ctx.rotate(-roll * Math.PI / 180);

    const pitchPx = (pitch / 90) * (R * 1.4);
    const gradSky = ctx.createLinearGradient(0, -R, 0, 0);
    gradSky.addColorStop(0, '#0d223a');
    gradSky.addColorStop(1, '#1f6feb');
    ctx.fillStyle = gradSky;
    ctx.fillRect(-W, -H + pitchPx, W*2, H);

    const gradGnd = ctx.createLinearGradient(0, 0, 0, R);
    gradGnd.addColorStop(0, '#3d1f05');
    gradGnd.addColorStop(1, '#1a0b00');
    ctx.fillStyle = gradGnd;
    ctx.fillRect(-W, pitchPx, W*2, H);

    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(-W, pitchPx);
    ctx.lineTo(W, pitchPx);
    ctx.stroke();

    for (let deg = -40; deg <= 40; deg += 10) {
      if (deg === 0) continue;
      const y = pitchPx - (deg / 90) * (R * 1.4);
      const lineW = (Math.abs(deg) % 20 === 0) ? 60 : 30;
      ctx.strokeStyle = 'rgba(255,255,255,0.7)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(-lineW, y);
      ctx.lineTo(lineW, y);
      ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.font = '12px monospace';
      ctx.fillText(`${deg > 0 ? '+'+deg : deg}°`, lineW + 6, y + 4);
    }
    ctx.restore();

    ctx.save();
    ctx.translate(CX, CY);
    ctx.rotate(-yaw * Math.PI / 180);
    ctx.strokeStyle = 'rgba(255, 123, 0, 0.4)';
    ctx.lineWidth = 2;
    for (let i = 0; i < 360; i += 30) {
      ctx.save();
      ctx.rotate(i * Math.PI / 180);
      ctx.beginPath();
      ctx.moveTo(0, -R + 5);
      ctx.lineTo(0, -R + 15);
      ctx.stroke();
      ctx.restore();
    }
    ctx.fillStyle = '#ff7b00';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('N', 0, -R + 32);
    ctx.fillText('S', 0,  R - 18);
    ctx.fillText('E',  R - 22, 6);
    ctx.fillText('W', -R + 22, 6);
    ctx.restore();

    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(CX - 70, CY);
    ctx.lineTo(CX - 25, CY);
    ctx.lineTo(CX - 15, CY + 15);
    ctx.moveTo(CX + 70, CY);
    ctx.lineTo(CX + 25, CY);
    ctx.lineTo(CX + 15, CY + 15);
    ctx.stroke();

    ctx.fillStyle = '#ff7b00';
    ctx.beginPath();
    ctx.arc(CX, CY, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    ctx.strokeStyle = (flightState === 1) ? '#ff3333' : '#ff7b00';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.arc(CX, CY, R + 2, 0, Math.PI * 2);
    ctx.stroke();
  }

  let lastData = {};
  async function pollServer() {
    try {
      const res = await fetch('/api/xedua/state');
      const d = await res.json();
      lastData = d;

      const conn = document.getElementById('connPill');
      if (d.online) {
        conn.className = 'pill online';
        conn.innerText = '● XE ONLINE (NguyenNgocTai)';
      } else {
        conn.className = 'pill offline';
        conn.innerText = '● XE OFFLINE (Chưa thấy UDP)';
      }

      document.getElementById('ipPill').innerText = 'IP XE: ' + (d.ip || '---');
      document.getElementById('jumpPill').innerText = 'NHẢY DỐC: ' + (d.jumps || 0) + ' LẦN';

      document.getElementById('vPitch').innerText = (d.pitch >= 0 ? '+' : '') + d.pitch.toFixed(1) + '°';
      document.getElementById('vRoll').innerText  = (d.roll  >= 0 ? '+' : '') + d.roll.toFixed(1) + '°';
      document.getElementById('vYaw').innerText   = Math.round(d.yaw) + '°';
      document.getElementById('vG').innerText     = d.g.toFixed(2) + 'G';
      document.getElementById('vThr').innerText   = d.thr + '%';
      document.getElementById('vEsc').innerText   = Math.round(d.esc) + ' µs';
      document.getElementById('vStr').innerText   = d.str + '%';
      document.getElementById('vSrv').innerText   = Math.round(d.srv) + '°';

      const curSpd = (d.spd !== undefined) ? d.spd : 0.0;
      const maxSpd = (d.maxSpd !== undefined) ? d.maxSpd : 0.0;
      const jmpSpd = (d.jmpSpd !== undefined) ? d.jmpSpd : 0.0;
      const spdCap = (d.cap !== undefined) ? d.cap : 100;

      document.getElementById('vSpd').innerHTML = curSpd.toFixed(1) + ' <span style="font-size:0.8rem">km/h</span>';
      document.getElementById('vMaxSpd').innerHTML = maxSpd.toFixed(1) + ' <span style="font-size:0.8rem">km/h</span>';
      document.getElementById('vJmpSpd').innerHTML = jmpSpd.toFixed(1) + ' <span style="font-size:0.8rem">km/h</span>';

      const barPct = Math.min(100, Math.max(0, (curSpd / 50.0) * 100));
      document.getElementById('spdBar').style.width = barPct + '%';

      if (curSpd > 6.0) {
        isCarRunning = true;
        if (curSpd > topSpeedThisRun) topSpeedThisRun = curSpd;
      } else if (isCarRunning && curSpd < 2.0) {
        recordSpeedCap(topSpeedThisRun, "Tự động chốt khi phanh dừng");
        isCarRunning = false;
        topSpeedThisRun = 0.0;
      }

      document.getElementById('mmPitch').innerText = `Min: ${d.minP.toFixed(1)}° | Max: +${d.maxP.toFixed(1)}°`;
      document.getElementById('mmRoll').innerText  = `Max nghiêng: ${d.maxR.toFixed(1)}°`;
      document.getElementById('mmG').innerText     = `Min: ${d.minG.toFixed(2)}G | Max: ${d.maxG.toFixed(2)}G`;

      const fTxt = document.getElementById('flightStateTxt');
      const jumpP = document.getElementById('jumpPill');
      const corrBox = document.getElementById('corrBox');
      if (d.air === 1) {
        fTxt.innerText = 'ĐANG BAY TRÊN KHÔNG!';
        fTxt.style.color = '#ff3333';
        jumpP.className = 'pill air';
        corrBox.style.background = '#4a1505';
        corrBox.style.borderColor = '#ff3333';
        corrBox.innerText = `CẢNH BÁO BAY DỐC: ${d.corr === 1 ? 'DÌM MŨI PHANH -85%' : (d.corr === 2 ? 'NHẤC MŨI BỒI GA +85%' : 'GIỮ THĂNG BẰNG 0%')}`;
      } else if (d.air === 2) {
        fTxt.innerText = 'VỪA TIẾP ĐẤT!';
        fTxt.style.color = '#ffd33d';
        jumpP.className = 'pill';
        corrBox.style.background = '#2e2605';
        corrBox.style.borderColor = '#ffd33d';
        corrBox.innerText = 'TIẾP ĐẤT AN TOÀN - ĐÃ HOÀN TRẢ QUYỀN GA 1:1 CHO TAY CẦM';
      } else {
        fTxt.innerText = 'MẶT ĐẤT';
        fTxt.style.color = '#58a6ff';
        jumpP.className = 'pill';
        corrBox.style.background = '#161b22';
        corrBox.style.borderColor = '#30363d';
        corrBox.innerText = 'TRẠNG THÁI: XE ĐANG ĐỨNG YÊN / CHẠY TRÊN ĐƯỜNG ĐUA';
      }

      if (d.ota_msg) document.getElementById('otaLog').innerText = 'Trạng thái OTA: ' + d.ota_msg;
      drawHorizon(d.pitch, d.roll, d.yaw, d.air);
    } catch (e) {}
    setTimeout(pollServer, 80);
  }

  function recordSpeedCap(spd, note) {
    if (spd < 3.0) return;
    const nowStr = new Date().toLocaleTimeString();
    speedCapHistory.unshift({time: nowStr, spd: spd.toFixed(1), note: note});
    if (speedCapHistory.length > 8) speedCapHistory.pop();
    renderCapList();
  }

  function capSpeedRun() {
    const cur = (lastData && lastData.spd) ? lastData.spd : 0.0;
    recordSpeedCap(cur, "Bấm chụp thủ công");
  }

  function renderCapList() {
    const el = document.getElementById('capList');
    if (!el || speedCapHistory.length === 0) return;
    el.innerHTML = speedCapHistory.map((item, idx) =>
      `<div>[${item.time}] <b>Lượt #${idx+1}:</b> <span style="color:#00e5ff;font-weight:bold">${item.spd} km/h</span> - <i>${item.note}</i></div>`
    ).join('');
  }

  async function zeroIMU() {
    const r = await fetch('/api/xedua/zero_imu', {method:'POST'});
    const j = await r.json();
    alert(j.message);
  }

  async function applyTune() {
    const tp  = document.getElementById('sTp').value;
    const fg  = document.getElementById('sFg').value;
    const brk = document.getElementById('sBrk').value;
    const pch = document.getElementById('sPch').value;
    const cap = document.getElementById('sCap').value;
    const r = await fetch(`/api/tune?tp=${tp}&fg=${fg}&brk=${brk}&pch=${pch}&cap=${cap}`, {method:'POST'});
    const j = await r.json();
    alert(j.message);
  }

  function copyForAI() {
    if (!lastData) { alert('Chưa có dữ liệu IMU!'); return; }
    const txt = `DỮ LIỆU ĐO IMU TỪ XE:\n- Pitch: ${lastData.pitch}° (Min: ${lastData.minP}°, Max: ${lastData.maxP}°)\n- Roll: ${lastData.roll}° (Max: ${lastData.maxR}°)\n- Yaw: ${lastData.yaw}°\n- G-Force: ${lastData.g}G (Min: ${lastData.minG}G, Max: ${lastData.maxG}G)\n- Ga/Xung ESC: ${lastData.thr}% (${Math.round(lastData.esc)}us)\n- Số lần bay dốc: ${lastData.jumps}\n- Trạng thái bay: ${lastData.air === 1 ? 'ĐANG BAY' : (lastData.air === 2 ? 'TIẾP ĐẤT' : 'MẶT ĐẤT')}`;
    navigator.clipboard.writeText(txt).then(() => alert('Đã copy dữ liệu IMU vào Clipboard! Bạn có thể dán (Ctrl+V) gửi cho AI phân tích.'));
  }

  async function triggerInstantOTA() {
    if (!confirm('Nạp ngay file .bin mới nhất trong máy tính vào xe qua WiFi NguyenNgocTai?')) return;
    document.getElementById('otaLog').innerText = 'Đang gửi lệnh nạp Cloud OTA xuống xe...';
    const r = await fetch('/api/xedua/ota_flash', {method:'POST'});
    const j = await r.json();
    alert(j.message);
  }

  async function compileAndOTA() {
    if (!confirm('Tự động biên dịch lại code xe_racing_s3.ino và nạp thẳng qua WiFi vào xe?')) return;
    document.getElementById('otaLog').innerText = 'Đang biên dịch xe_racing_s3.ino... Vui lòng chờ khoảng 20-30 giây...';
    const r = await fetch('/api/ota/compile_and_flash', {method:'POST'});
    const j = await r.json();
    alert(j.message);
  }

  async function switchCarToRace() {
    const r = await fetch('/api/xedua/switch_race', {method:'POST'});
    const j = await r.json();
    alert(j.message);
  }

  drawHorizon();
  pollServer();
</script>
</body>
</html>
"""

@xedua_bp.route("/xedua")
@xedua_bp.route("/xedua/")
def xedua_index():
    resp = Response(DASHBOARD_HTML, mimetype="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

@xedua_bp.route("/xedua/led")
def xedua_led_page():
    html = DASHBOARD_HTML.replace("switchMainTab('race')", "switchMainTab('led')")
    html = html.replace('id="tabRaceContent" class="tab-content active"', 'id="tabRaceContent" class="tab-content"')
    html = html.replace('id="tabLedContent" class="tab-content"', 'id="tabLedContent" class="tab-content active"')
    html = html.replace('id="navTabRace" class="nav-btn active"', 'id="navTabRace" class="nav-btn"')
    html = html.replace('id="navTabLed" class="nav-btn led-tab"', 'id="navTabLed" class="nav-btn led-tab active"')
    resp = Response(html, mimetype="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

@xedua_bp.route("/api/xedua/state")
def api_state():
    if time.time() - car_state["last_seen"] > 4.5:
        car_state["online"] = False
    return jsonify(car_state)

@xedua_bp.route("/api/xedua/led", methods=["GET", "POST"])
def api_led():
    global led_config
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        led_config.update(data)
        save_led_config(led_config)
        return jsonify({"status": "ok", "message": "?? l?u l?n Render Cloud (Xe s? t? ??ng b?)", "config": led_config})
    return jsonify({"status": "ok", "config": led_config})

@xedua_bp.route("/api/xedua/led/test", methods=["POST"])
def api_led_test():
    data = request.get_json(force=True, silent=True) or {}
    act = data.get("action", "off")
    in_mode = data.get("intro_mode", led_config.get("intro_mode", "audi_rs"))
    pending_commands["test_action"] = act
    pending_commands["test_in_mode"] = in_mode
    return jsonify({"status": "ok", "message": f"?? g?i l?nh test {act} l?n Cloud!"})

@xedua_bp.route("/api/xedua/tune", methods=["POST"])
def api_tune():
    qs = request.query_string.decode("utf-8")
    pending_commands["tune_qs"] = qs
    return jsonify({"status": "ok", "message": "?? c?p nh?t th?ng s? l?n Render Cloud!"})

@xedua_bp.route("/api/xedua/zero_imu", methods=["POST"])
def api_zero_imu():
    pending_commands["zero_imu"] = True
    return jsonify({"status": "ok", "message": "?? y?u c?u ??t l?i g?c 0? IMU!"})

@xedua_bp.route("/api/xedua/ota_flash", methods=["POST"])
def api_ota_flash():
    host = request.host_url.rstrip("/")
    fw_url = f"{host}/api/firmware/xe_racing_s3.ino.bin"
    pending_commands["ota_url"] = fw_url
    car_state["ota_msg"] = f"?? g?i l?nh n?p Cloud OTA ({fw_url}) xu?ng xe!"
    return jsonify({"status": "ok", "message": f"?? ph?t l?nh n?p Cloud OTA t? Render!\nXe s? t? ??ng t?i firmware t?: {fw_url}"})

@xedua_bp.route("/api/xedua/sync", methods=["POST"])
def api_car_sync():
    data = request.get_json(force=True, silent=True) or {}
    car_state.update(data)
    car_state["last_seen"] = time.time()
    car_state["online"] = True

    car_cfg_ver = data.get("cfg_ver", 0)
    need_cfg = (car_cfg_ver != cfg_version)

    resp = {
        "status": "ok",
        "cfg_ver": cfg_version,
        "config": led_config if need_cfg else None,
        "test_action": pending_commands.get("test_action"),
        "test_in_mode": pending_commands.get("test_in_mode"),
        "zero_imu": pending_commands.get("zero_imu"),
        "tune_qs": pending_commands.get("tune_qs"),
        "ota_url": pending_commands.get("ota_url")
    }

    pending_commands["test_action"] = None
    pending_commands["zero_imu"] = False
    pending_commands["tune_qs"] = None
    pending_commands["ota_url"] = None

    return jsonify(resp)

def register_xedua(app):
    app.register_blueprint(xedua_bp)
    print("[XEDUA] Registered Racing Car Studio routes on /xedua & /xedua/led")

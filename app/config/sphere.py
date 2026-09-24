SPHERE_WIDGET_MIN_SIZE: int = 200
SPHERE_FRAME_INTERVAL_MS: int = 16
SPHERE_MAX_FRAME_DELTA_S: float = 0.05
SPHERE_MIN_TIME_CONSTANT_S: float = 0.001
SPHERE_VISIBILITY_THRESHOLD: float = 0.01
SPHERE_DEFORMATION_THRESHOLD: float = 0.0001

SPHERE_BASE_RADIUS: float = 100.0
SPHERE_VIEWPORT_FILL: float = 0.92
SPHERE_MAX_BODY_SCALE: float = 1.4
SPHERE_OUTLINE_SEGMENTS: int = 180
SPHERE_DRIFT_PERIOD_S: float = 7.5
SPHERE_INHALE_RATIO_LIMITS: tuple[float, float] = (0.05, 0.95)

SPHERE_BODY_FOCAL_OFFSET: tuple[float, float] = (-0.22, -0.28)
SPHERE_BODY_HIGHLIGHT_LIGHTEN: int = 125
SPHERE_BODY_STOP_MID: float = 0.62

SPHERE_CORE_STOP_MID: float = 0.45
SPHERE_CORE_MID_ALPHA_RATIO: float = 0.55

SPHERE_HALO_FALLOFF_STOP: float = 0.35
SPHERE_HALO_FALLOFF_ALPHA_RATIO: float = 0.35
SPHERE_HALO_VOICE_BOOST: float = 0.6

SPHERE_RIM_STOP_START: float = 0.76
SPHERE_RIM_STOP_PEAK: float = 0.96
SPHERE_RIM_EDGE_ALPHA_RATIO: float = 0.7
SPHERE_RIM_VOICE_BOOST: float = 0.5

SPHERE_SMOKE_COLOR: str = "#05020b"
SPHERE_SMOKE_STOP_START: float = 0.3

SPHERE_SPECULAR_COLOR: str = "#ffffff"
SPHERE_SPECULAR_OFFSET: tuple[float, float] = (-0.34, -0.46)
SPHERE_SPECULAR_SIZE: tuple[float, float] = (0.5, 0.28)
SPHERE_SPECULAR_ROTATION_DEG: float = -32.0
SPHERE_SPECULAR_ALPHA: float = 0.32

SPHERE_CHROMATIC_COLORS: tuple[str, ...] = ("#ffd1ec", "#c9e8ff", "#d4ffe9", "#e4d4ff", "#ffd1ec")
SPHERE_CHROMATIC_RING_RADIUS: float = 1.04
SPHERE_CHROMATIC_RING_LAYERS: tuple[tuple[float, float], ...] = ((0.05, 0.45), (0.11, 0.22), (0.2, 0.1))
SPHERE_CHROMATIC_SPIN_SPEED_DEG: float = 25.0

SPHERE_SWIRL_BLOBS: tuple[tuple[float, float, float, float, bool, float], ...] = (
    (0.38, 0.55, 1.0, 0.0, True, 0.55),
    (0.52, 0.42, -0.7, 2.1, False, 0.5),
    (0.22, 0.48, 1.4, 4.0, True, 0.4),
    (0.6, 0.35, 0.55, 1.2, False, 0.45),
    (0.45, 0.3, -1.2, 5.1, True, 0.35),
)
SPHERE_SWIRL_TILT: float = 0.8
SPHERE_SWIRL_WOBBLE: float = 0.18
SPHERE_SWIRL_WOBBLE_SPEED: float = 0.6

SPHERE_NODE_ELLIPSE_RATIO: float = 0.55
SPHERE_NODE_PRECESSION_SPEED: float = 0.35
SPHERE_NODE_RADIUS_RATIO: float = 0.06
SPHERE_NODE_GLOW_RATIO: float = 2.6
SPHERE_NODE_HEAD_LIGHTEN: int = 160
SPHERE_NODE_TRAIL_SEGMENTS: int = 22
SPHERE_NODE_TRAIL_SPACING: float = 0.07
SPHERE_NODE_TRAIL_REFERENCE_SPEED: float = 3.2
SPHERE_NODE_TRAIL_ALPHA: float = 0.22
SPHERE_NODE_TRAIL_MIN_SIZE_RATIO: float = 0.35

SPHERE_MOTE_COLOR: str = "#ffffff"
SPHERE_MOTE_SPAWN_PER_S: float = 70.0
SPHERE_MOTE_MAX_COUNT: int = 160
SPHERE_MOTE_START_DISTANCE: tuple[float, float] = (0.85, 1.02)
SPHERE_MOTE_END_DISTANCE: float = 0.04
SPHERE_MOTE_SPEED: tuple[float, float] = (0.25, 0.6)
SPHERE_MOTE_SIZE: tuple[float, float] = (1.2, 2.8)
SPHERE_MOTE_SPIRAL_SPEED: float = 0.6
SPHERE_MOTE_SPIRAL_MIN_DISTANCE: float = 0.25
SPHERE_MOTE_GLOW_RATIO: float = 2.5
SPHERE_MOTE_FADE_GAIN: float = 2.5

SPHERE_BODY_WAVES: tuple[tuple[int, float, float, float], ...] = (
    (2, 1.6, 0.6, 0.0),
    (3, -2.2, 0.4, 1.3),
)
SPHERE_RIPPLE_WAVES: tuple[tuple[int, float, float, float], ...] = (
    (5, 5.5, 0.45, 0.4),
    (8, -7.5, 0.35, 2.2),
    (13, 9.0, 0.2, 4.1),
)
SPHERE_HUM_WAVES: tuple[tuple[int, float, float, float], ...] = (
    (23, 41.0, 0.5, 0.0),
    (31, -37.0, 0.5, 1.7),
)

SPHERE_VOICE_RISE_S: float = 0.05
SPHERE_VOICE_FALL_S: float = 0.14
SPHERE_VOICE_ENVELOPE_S: float = 0.35
SPHERE_VOICE_TRANSIENT_GAIN: float = 2.5

SPHERE_LOOK_DEFAULT: dict[str, float | str] = {
    "scale_min": 0.98,
    "scale_max": 1.02,
    "breath_period_s": 3.6,
    "inhale_ratio": 0.45,
    "drift_px": 2.5,
    "body_color": "#c27b22",
    "edge_color": "#5a300e",
    "edge_alpha": 0.6,
    "core_color": "#ffd88a",
    "core_intensity": 0.7,
    "core_extent": 0.55,
    "rim_color": "#ffe4bd",
    "rim_alpha": 0.35,
    "halo_color": "#c98a2e",
    "halo_alpha": 0.16,
    "halo_extent": 1.45,
    "chromatic": 0.0,
    "smoke": 0.0,
    "swirl": 0.6,
    "swirl_speed": 0.35,
    "swirl_light": "#ffb347",
    "swirl_dark": "#5a2a0a",
    "nodes": 0.0,
    "node_orbit": 0.55,
    "node_speed": 1.2,
    "node_color": "#e0b3ff",
    "motes": 0.0,
    "hum": 0.0,
    "voice_expansion": 0.0,
    "voice_body": 0.0,
    "voice_ripple": 0.0,
    "transition_s": 0.45,
}

SPHERE_LOOK_LISTENING: dict[str, float | str] = {
    "scale_min": 1.235,
    "scale_max": 1.265,
    "breath_period_s": 2.6,
    "inhale_ratio": 0.5,
    "drift_px": 0.8,
    "body_color": "#1f6bff",
    "edge_color": "#0a2a8c",
    "edge_alpha": 0.6,
    "core_color": "#7fd4ff",
    "core_intensity": 0.85,
    "core_extent": 0.6,
    "rim_color": "#5ff3ff",
    "rim_alpha": 0.6,
    "halo_color": "#2f8fff",
    "halo_alpha": 0.32,
    "halo_extent": 1.65,
    "chromatic": 0.0,
    "smoke": 0.0,
    "swirl": 0.25,
    "swirl_speed": 0.9,
    "swirl_light": "#9be7ff",
    "swirl_dark": "#08206b",
    "nodes": 0.0,
    "node_orbit": 0.55,
    "node_speed": 1.2,
    "node_color": "#e0b3ff",
    "motes": 0.0,
    "hum": 0.0,
    "voice_expansion": 0.03,
    "voice_body": 0.02,
    "voice_ripple": 0.035,
    "transition_s": 0.12,
}

SPHERE_LOOK_THINKING: dict[str, float | str] = {
    "scale_min": 1.07,
    "scale_max": 1.10,
    "breath_period_s": 1.5,
    "inhale_ratio": 0.5,
    "drift_px": 0.0,
    "body_color": "#4b1fa8",
    "edge_color": "#140828",
    "edge_alpha": 0.75,
    "core_color": "#8e44ff",
    "core_intensity": 0.5,
    "core_extent": 0.45,
    "rim_color": "#b388ff",
    "rim_alpha": 0.4,
    "halo_color": "#5b2bd6",
    "halo_alpha": 0.2,
    "halo_extent": 1.4,
    "chromatic": 0.0,
    "smoke": 0.45,
    "swirl": 0.12,
    "swirl_speed": 1.5,
    "swirl_light": "#c77dff",
    "swirl_dark": "#12062b",
    "nodes": 1.0,
    "node_orbit": 0.55,
    "node_speed": 3.2,
    "node_color": "#e0b3ff",
    "motes": 0.0,
    "hum": 0.0,
    "voice_expansion": 0.0,
    "voice_body": 0.0,
    "voice_ripple": 0.0,
    "transition_s": 0.22,
}

SPHERE_LOOK_RENDERING: dict[str, float | str] = {
    "scale_min": 1.10,
    "scale_max": 1.10,
    "breath_period_s": 1.5,
    "inhale_ratio": 0.5,
    "drift_px": 0.0,
    "body_color": "#e6ecf5",
    "edge_color": "#9fb8d6",
    "edge_alpha": 0.8,
    "core_color": "#ffffff",
    "core_intensity": 0.95,
    "core_extent": 0.7,
    "rim_color": "#dfe9ff",
    "rim_alpha": 0.5,
    "halo_color": "#cfe3ff",
    "halo_alpha": 0.28,
    "halo_extent": 1.55,
    "chromatic": 0.7,
    "smoke": 0.0,
    "swirl": 0.05,
    "swirl_speed": 0.6,
    "swirl_light": "#ffffff",
    "swirl_dark": "#b8c7dd",
    "nodes": 0.8,
    "node_orbit": 0.04,
    "node_speed": 1.0,
    "node_color": "#f4f0ff",
    "motes": 1.0,
    "hum": 0.008,
    "voice_expansion": 0.0,
    "voice_body": 0.0,
    "voice_ripple": 0.0,
    "transition_s": 0.5,
}

SPHERE_LOOK_SPEAKING: dict[str, float | str] = {
    "scale_min": 1.17,
    "scale_max": 1.19,
    "breath_period_s": 4.0,
    "inhale_ratio": 0.45,
    "drift_px": 0.0,
    "body_color": "#ffffff",
    "edge_color": "#e8eef7",
    "edge_alpha": 0.75,
    "core_color": "#ffffff",
    "core_intensity": 1.0,
    "core_extent": 0.75,
    "rim_color": "#ffffff",
    "rim_alpha": 0.55,
    "halo_color": "#ffffff",
    "halo_alpha": 0.3,
    "halo_extent": 1.7,
    "chromatic": 0.1,
    "smoke": 0.0,
    "swirl": 0.0,
    "swirl_speed": 0.4,
    "swirl_light": "#ffffff",
    "swirl_dark": "#e8eef7",
    "nodes": 0.0,
    "node_orbit": 0.04,
    "node_speed": 1.0,
    "node_color": "#ffffff",
    "motes": 0.0,
    "hum": 0.0,
    "voice_expansion": 0.1,
    "voice_body": 0.04,
    "voice_ripple": 0.025,
    "transition_s": 0.08,
}

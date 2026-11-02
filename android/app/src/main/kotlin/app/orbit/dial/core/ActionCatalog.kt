package app.orbit.dial.core

/**
 * Categories of customizable actions.
 */
enum class ActionCategory(val title: String) {
    AUDIO("Volume & Audio"),
    SCREEN("Screen & Display"),
    NAVIGATION("Navigation"),
    CAMERA("Camera"),
    PRODUCTIVITY("Productivity")
}

/**
 * Definition of an individual assignable action.
 */
data class ActionDefinition(
    val id: String,
    val name: String,
    val description: String,
    val category: ActionCategory,
    val iconResName: String,
    val requiresAccessibility: Boolean = false,
    val requiresWriteSettings: Boolean = false,
    val requiresNotificationListener: Boolean = false
)

/**
 * Universal Action Catalog for Orbit.
 */
object ActionCatalog {

    val ACTIONS = listOf(
        // Audio
        ActionDefinition(
            id = "action:volume_up",
            name = "Volume Up",
            description = "Raise music playback volume",
            category = ActionCategory.AUDIO,
            iconResName = "ic_volume"
        ),
        ActionDefinition(
            id = "action:volume_down",
            name = "Volume Down",
            description = "Lower music playback volume",
            category = ActionCategory.AUDIO,
            iconResName = "ic_volume"
        ),
        ActionDefinition(
            id = "action:mute_toggle",
            name = "Mute / Unmute",
            description = "Mute or restore music volume",
            category = ActionCategory.AUDIO,
            iconResName = "ic_mute"
        ),
        ActionDefinition(
            id = "action:play_pause",
            name = "Play / Pause",
            description = "Toggle active media playback",
            category = ActionCategory.AUDIO,
            iconResName = "ic_play",
            requiresNotificationListener = true
        ),
        ActionDefinition(
            id = "action:next_track",
            name = "Next Track",
            description = "Skip to the next song or video",
            category = ActionCategory.AUDIO,
            iconResName = "ic_play",
            requiresNotificationListener = true
        ),
        ActionDefinition(
            id = "action:prev_track",
            name = "Previous Track",
            description = "Restart or skip to previous song",
            category = ActionCategory.AUDIO,
            iconResName = "ic_play",
            requiresNotificationListener = true
        ),

        // Screen
        ActionDefinition(
            id = "action:brightness_up",
            name = "Brightness Up",
            description = "Increase screen brightness",
            category = ActionCategory.SCREEN,
            iconResName = "ic_brightness",
            requiresWriteSettings = true
        ),
        ActionDefinition(
            id = "action:brightness_down",
            name = "Brightness Down",
            description = "Decrease screen brightness",
            category = ActionCategory.SCREEN,
            iconResName = "ic_brightness",
            requiresWriteSettings = true
        ),
        ActionDefinition(
            id = "action:flashlight_toggle",
            name = "Flashlight Toggle",
            description = "Turn device LED torch on or off",
            category = ActionCategory.SCREEN,
            iconResName = "ic_bolt"
        ),

        // Navigation
        ActionDefinition(
            id = "action:scroll_up",
            name = "Scroll Up",
            description = "Smoothly scroll page up",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_scroll",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:scroll_down",
            name = "Scroll Down",
            description = "Smoothly scroll page down",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_scroll",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:page_up",
            name = "Page Up",
            description = "Flick page up (Reels / TikTok / Reading)",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_scroll",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:page_down",
            name = "Page Down",
            description = "Flick page down (Reels / TikTok / Reading)",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_scroll",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:app_switch",
            name = "Switch App",
            description = "Cycle to previous recent app",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_tabs",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:back",
            name = "Back",
            description = "Perform Android back navigation",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_arrow_left",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:home",
            name = "Home",
            description = "Navigate to home screen",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_app",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:notifications",
            name = "Open Notifications",
            description = "Expand system notification shade",
            category = ActionCategory.NAVIGATION,
            iconResName = "ic_settings",
            requiresAccessibility = true
        ),

        // Camera
        ActionDefinition(
            id = "action:camera_zoom_in",
            name = "Camera Zoom In",
            description = "Zoom in viewfinder via pinch gesture",
            category = ActionCategory.CAMERA,
            iconResName = "ic_zoom",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:camera_zoom_out",
            name = "Camera Zoom Out",
            description = "Zoom out viewfinder via pinch gesture",
            category = ActionCategory.CAMERA,
            iconResName = "ic_zoom",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:camera_shutter",
            name = "Camera Shutter",
            description = "Snap photo or start/stop recording",
            category = ActionCategory.CAMERA,
            iconResName = "ic_camera",
            requiresAccessibility = true
        ),

        // Productivity
        ActionDefinition(
            id = "action:undo",
            name = "Undo",
            description = "Undo last text or editor action",
            category = ActionCategory.PRODUCTIVITY,
            iconResName = "ic_undo",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:redo",
            name = "Redo",
            description = "Redo last text or editor action",
            category = ActionCategory.PRODUCTIVITY,
            iconResName = "ic_redo",
            requiresAccessibility = true
        ),
        ActionDefinition(
            id = "action:assistant",
            name = "Voice Assistant / Claude",
            description = "Launch digital assistant or Claude voice",
            category = ActionCategory.PRODUCTIVITY,
            iconResName = "ic_claude"
        )
    )

    fun find(actionId: String): ActionDefinition? = ACTIONS.firstOrNull { it.id == actionId }
}


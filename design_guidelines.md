{
  "brand": {
    "product_name": "Kaelra",
    "tagline_internal": "Personal AI Operator — warm, proactive chief-of-staff",
    "brand_attributes": [
      "premium",
      "futuristic",
      "warm",
      "trustworthy",
      "alive/present",
      "safety-forward (approval-first)"
    ],
    "anti_patterns": [
      "generic chat app layout (full-height message list + composer only)",
      "purple-heavy AI aesthetic",
      "centered-everything landing-page hero",
      "busy neon gradients covering large areas",
      "flat/static empty states"
    ]
  },

  "inspiration_refs": {
    "search_refs": [
      {
        "title": "Dribbble: AI Assistant Motion (orb/presence)",
        "url": "https://dribbble.com/shots/25879297-Ai-Assistant-Motion",
        "takeaways": [
          "Orb as a living presence with subtle motion",
          "Use glow as state indicator (thinking/listening)",
          "Keep UI minimal around the orb; let it breathe"
        ]
      },
      {
        "title": "Dribbble search: glassmorphism dark mode",
        "url": "https://dribbble.com/search/glassmorphism-dark-mode",
        "takeaways": [
          "Frosted panels + thin borders + soft highlights",
          "Dark canvas with restrained accent glows",
          "Cards feel layered (depth)"
        ]
      },
      {
        "title": "Dribbble: AI Assistant Mobile App UI (futuristic prompt generator)",
        "url": "https://dribbble.com/shots/27073005-AI-Assistant-Mobile-App-UI-Futuristic-Prompt-Generator-Design",
        "takeaways": [
          "Command-like input with suggestions",
          "Premium dark surfaces with subtle glow",
          "Prompt chips as fast actions"
        ]
      },
      {
        "title": "Dribbble tags/search: command bar",
        "url": "https://dribbble.com/tags/command-bar",
        "takeaways": [
          "Command bar as primary interaction model",
          "Keyboard-first affordances on desktop",
          "Compact, high-signal UI"
        ]
      }
    ]
  },

  "typography": {
    "google_fonts": {
      "heading": {
        "family": "Space Grotesk",
        "weights": ["500", "600", "700"],
        "usage": "Headings, section titles, key numbers"
      },
      "body": {
        "family": "Figtree",
        "weights": ["400", "500", "600"],
        "usage": "Body, labels, helper text"
      },
      "mono": {
        "family": "IBM Plex Mono",
        "weights": ["400", "500"],
        "usage": "Timestamps, IDs, integration states, technical metadata"
      }
    },
    "tailwind_mapping": {
      "font_heading": "font-[var(--font-heading)]",
      "font_body": "font-[var(--font-body)]",
      "font_mono": "font-[var(--font-mono)]"
    },
    "type_scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs text-muted-foreground",
      "kicker": "text-xs uppercase tracking-[0.18em]"
    },
    "copy_tone": {
      "kaelra_voice": "Warm, concise, proactive. Uses short paragraphs and bullet-like lines. Avoids exclamation spam.",
      "status_microcopy_examples": [
        "Kaelra is checking your day…",
        "Synced on this device",
        "Prepared 3 actions — waiting for your approval",
        "Last briefing updated 2 minutes ago"
      ]
    }
  },

  "color_system": {
    "mode": "dark-first",
    "notes": [
      "No purple-forward palette.",
      "Use ocean-teal + warm amber as the signature contrast (cool intelligence + warm humanity).",
      "Glass cards must keep text readable: use light text on dark translucent surfaces."
    ],
    "tokens_hsl_for_shadcn": {
      "root_dark": {
        "--background": "220 18% 6%",
        "--foreground": "210 20% 96%",

        "--card": "220 18% 8%",
        "--card-foreground": "210 20% 96%",

        "--popover": "220 18% 8%",
        "--popover-foreground": "210 20% 96%",

        "--primary": "174 72% 44%",
        "--primary-foreground": "220 18% 8%",

        "--secondary": "220 14% 14%",
        "--secondary-foreground": "210 20% 96%",

        "--muted": "220 14% 14%",
        "--muted-foreground": "215 14% 70%",

        "--accent": "32 92% 58%",
        "--accent-foreground": "220 18% 8%",

        "--destructive": "0 72% 52%",
        "--destructive-foreground": "210 20% 96%",

        "--border": "220 14% 18%",
        "--input": "220 14% 18%",
        "--ring": "174 72% 44%",

        "--radius": "0.9rem"
      },
      "semantic": {
        "--success": "156 62% 42%",
        "--warning": "38 92% 56%",
        "--info": "199 84% 60%",
        "--pending": "174 72% 44%",
        "--sensitive": "12 86% 58%"
      }
    },
    "hex_palette_reference": {
      "bg_0": "#0B0F14",
      "bg_1": "#0F1620",
      "surface_glass": "rgba(255,255,255,0.06)",
      "surface_glass_strong": "rgba(255,255,255,0.10)",
      "stroke": "rgba(255,255,255,0.10)",
      "text": "#EAF0F7",
      "muted": "#A9B4C2",
      "teal": "#2DD4BF",
      "cyan": "#38BDF8",
      "amber": "#F59E0B",
      "danger": "#EF4444"
    },
    "allowed_gradients": {
      "bg_decorative_only": [
        "radial-gradient(900px circle at 20% 10%, rgba(45,212,191,0.18), transparent 55%)",
        "radial-gradient(700px circle at 80% 20%, rgba(56,189,248,0.14), transparent 60%)",
        "radial-gradient(800px circle at 60% 90%, rgba(245,158,11,0.10), transparent 55%)"
      ],
      "orb_core": [
        "radial-gradient(circle at 30% 30%, rgba(45,212,191,0.95), rgba(56,189,248,0.55) 35%, rgba(11,15,20,0.0) 70%)"
      ]
    }
  },

  "design_tokens_css": {
    "instructions": "Add these to /app/frontend/src/index.css under @layer base .dark (and set html/body to use .dark by default in app shell). Keep shadcn HSL tokens; add extra Kaelra tokens below.",
    "css": ":root{--font-heading:'Space Grotesk',ui-sans-serif,system-ui;--font-body:'Figtree',ui-sans-serif,system-ui;--font-mono:'IBM Plex Mono',ui-monospace,monospace;}\n.dark{\n  --kaelra-bg-0:#0B0F14;\n  --kaelra-bg-1:#0F1620;\n  --kaelra-glass:rgba(255,255,255,.06);\n  --kaelra-glass-strong:rgba(255,255,255,.10);\n  --kaelra-stroke:rgba(255,255,255,.10);\n  --kaelra-shadow:0 18px 60px rgba(0,0,0,.55);\n  --kaelra-shadow-soft:0 10px 30px rgba(0,0,0,.35);\n  --kaelra-noise-opacity:.06;\n  --kaelra-orb-teal:45 212 191;\n  --kaelra-orb-cyan:56 189 248;\n  --kaelra-orb-amber:245 158 11;\n  --kaelra-radius-card:18px;\n  --kaelra-radius-pill:999px;\n  --kaelra-focus:0 0 0 3px rgba(45,212,191,.22);\n}\n::selection{background:rgba(45,212,191,.25);}\n"
  },

  "layout": {
    "app_shell": {
      "mobile": {
        "pattern": "Bottom tab bar + top presence strip",
        "tabs": ["Today", "Talk", "Queue", "Memory", "Settings"],
        "safe_area": "Use pb-[env(safe-area-inset-bottom)] for tab bar"
      },
      "desktop": {
        "pattern": "Left sidebar + top command/presence bar + 12-col content grid",
        "sidebar_width": "w-[280px] xl:w-[320px]",
        "content_max": "max-w-[1400px]",
        "grid": "grid grid-cols-12 gap-4 xl:gap-6"
      }
    },
    "today_dashboard": {
      "hero_row": "Orb + Daily Briefing card (spans 12 on mobile; 7/5 split on desktop)",
      "cards": [
        "Calendar",
        "Important Emails",
        "Reminders",
        "Commute/Leave-time",
        "News Brief",
        "Goals Progress",
        "Files Needing Attention",
        "Action Queue Preview",
        "Device Sync Status"
      ],
      "density": "Use generous spacing; cards should feel like modules in a command center, not a feed."
    }
  },

  "kaelra_orb_spec": {
    "purpose": "Signature presence element. Always visible in shell (small) and featured on Today/Talk (large).",
    "sizes": {
      "shell": "44px",
      "today_feature": "160px (mobile) / 220px (desktop)",
      "talk_feature": "200px (mobile) / 260px (desktop)"
    },
    "states": {
      "idle": {
        "motion": "slow breathing scale 1.0→1.03→1.0 (6–8s), subtle halo drift",
        "color": "teal/cyan",
        "status_text": "Kaelra is here"
      },
      "listening": {
        "motion": "gentle ripple rings expanding (opacity fade), slightly faster breath (3.5–4.5s)",
        "color": "cyan-forward",
        "status_text": "Listening…"
      },
      "thinking": {
        "motion": "orbiting particles + slow rotation of inner gradient (10–14s), shimmer",
        "color": "teal→cyan with tiny amber spark",
        "status_text": "Checking your day…"
      },
      "speaking": {
        "motion": "audio-reactive-ish pulse (fake with keyframes), brighter rim",
        "color": "teal with warm amber edge",
        "status_text": "Explaining…"
      },
      "offline": {
        "motion": "no pulse; dim",
        "color": "muted",
        "status_text": "Sync paused"
      }
    },
    "implementation_notes_js": {
      "css_classes": [
        "relative",
        "rounded-full",
        "bg-[radial-gradient(circle_at_30%_30%,rgba(45,212,191,0.95),rgba(56,189,248,0.55)_35%,rgba(11,15,20,0)_70%)]",
        "shadow-[0_0_0_1px_rgba(255,255,255,0.10),0_18px_60px_rgba(0,0,0,0.55)]"
      ],
      "keyframes": {
        "orb-breathe": "0%,100%{transform:scale(1)}50%{transform:scale(1.03)}",
        "orb-ripple": "0%{transform:scale(.85);opacity:.55}100%{transform:scale(1.35);opacity:0}",
        "orb-drift": "0%,100%{transform:translate3d(0,0,0)}50%{transform:translate3d(6px,-4px,0)}"
      },
      "reduced_motion": "Respect prefers-reduced-motion: reduce by disabling keyframes and using static glow."
    }
  },

  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui/",
      "use_components": [
        { "name": "button", "path": "/app/frontend/src/components/ui/button.jsx" },
        { "name": "card", "path": "/app/frontend/src/components/ui/card.jsx" },
        { "name": "badge", "path": "/app/frontend/src/components/ui/badge.jsx" },
        { "name": "tabs", "path": "/app/frontend/src/components/ui/tabs.jsx" },
        { "name": "command", "path": "/app/frontend/src/components/ui/command.jsx" },
        { "name": "input", "path": "/app/frontend/src/components/ui/input.jsx" },
        { "name": "textarea", "path": "/app/frontend/src/components/ui/textarea.jsx" },
        { "name": "dialog", "path": "/app/frontend/src/components/ui/dialog.jsx" },
        { "name": "sheet", "path": "/app/frontend/src/components/ui/sheet.jsx" },
        { "name": "drawer", "path": "/app/frontend/src/components/ui/drawer.jsx" },
        { "name": "scroll-area", "path": "/app/frontend/src/components/ui/scroll-area.jsx" },
        { "name": "separator", "path": "/app/frontend/src/components/ui/separator.jsx" },
        { "name": "skeleton", "path": "/app/frontend/src/components/ui/skeleton.jsx" },
        { "name": "calendar", "path": "/app/frontend/src/components/ui/calendar.jsx" },
        { "name": "progress", "path": "/app/frontend/src/components/ui/progress.jsx" },
        { "name": "switch", "path": "/app/frontend/src/components/ui/switch.jsx" },
        { "name": "select", "path": "/app/frontend/src/components/ui/select.jsx" },
        { "name": "sonner", "path": "/app/frontend/src/components/ui/sonner.jsx" }
      ]
    },

    "glass_card_recipe": {
      "use": "Wrap shadcn Card with Kaelra glass classes.",
      "tailwind": "bg-[var(--kaelra-glass)] backdrop-blur-md border border-[color:var(--kaelra-stroke)] rounded-[var(--kaelra-radius-card)] shadow-[var(--kaelra-shadow-soft)]",
      "header": "text-sm text-muted-foreground",
      "title": "font-[var(--font-heading)] tracking-[-0.02em]",
      "body": "text-sm md:text-base",
      "hover": "hover:bg-[var(--kaelra-glass-strong)] hover:border-white/15",
      "focus_within": "focus-within:shadow-[var(--kaelra-focus)]"
    },

    "command_bar": {
      "component": "command",
      "pattern": "Always-present command bar (bottom on mobile above tab bar; top center on desktop).",
      "tailwind_shell": "bg-[var(--kaelra-glass)] backdrop-blur-md border border-white/10 rounded-[999px] px-3 py-2 shadow-[var(--kaelra-shadow-soft)]",
      "input": "bg-transparent border-0 focus-visible:ring-0 text-sm md:text-base",
      "chips": "Use Button variant=secondary as pill chips; keep them subtle.",
      "data_testid": {
        "input": "global-command-bar-input",
        "submit": "global-command-bar-submit-button",
        "chip": "global-command-bar-suggestion-chip"
      }
    },

    "action_queue_cards": {
      "status_badges": {
        "pending": "bg-[rgba(45,212,191,0.14)] text-[rgb(153,246,228)] border border-[rgba(45,212,191,0.22)]",
        "approved": "bg-[rgba(34,197,94,0.14)] text-[rgb(134,239,172)] border border-[rgba(34,197,94,0.22)]",
        "rejected": "bg-[rgba(239,68,68,0.14)] text-[rgb(254,202,202)] border border-[rgba(239,68,68,0.22)]",
        "snoozed": "bg-[rgba(245,158,11,0.14)] text-[rgb(253,230,138)] border border-[rgba(245,158,11,0.22)]",
        "sensitive": "bg-[rgba(251,146,60,0.14)] text-[rgb(254,215,170)] border border-[rgba(251,146,60,0.22)]"
      },
      "buttons": {
        "approve": "Button (primary) with teal; label 'Approve'",
        "reject": "Button variant=secondary; label 'Reject'",
        "edit": "Button variant=ghost; label 'Edit'",
        "snooze": "Button variant=secondary; label 'Snooze'"
      },
      "safety_language": [
        "Sensitive action — waiting for your approval",
        "Kaelra prepared this because: <reason>",
        "Source: Gmail / Calendar / Files"
      ],
      "data_testid_examples": [
        "action-queue-item-approve-button",
        "action-queue-item-reject-button",
        "action-queue-item-edit-button",
        "action-queue-item-snooze-button",
        "action-queue-item-status-badge"
      ]
    },

    "navigation": {
      "desktop_sidebar": {
        "style": "Glass sidebar with grouped nav + small orb + sync status.",
        "tailwind": "bg-[var(--kaelra-glass)] backdrop-blur-md border-r border-white/10",
        "active_item": "bg-white/8 border border-white/10",
        "data_testid": {
          "nav_item": "app-nav-item",
          "logout": "app-logout-button"
        }
      },
      "mobile_tabbar": {
        "style": "Bottom frosted bar with 5 tabs; center tab can be Talk (orb icon).",
        "tailwind": "fixed bottom-0 left-0 right-0 bg-[rgba(15,22,32,0.72)] backdrop-blur-md border-t border-white/10",
        "data_testid": {
          "tab": "mobile-tabbar-item"
        }
      }
    },

    "empty_loading_states": {
      "principle": "Empty states must feel alive: show orb mini + 1–2 lines of proactive copy + a suggested action chip.",
      "loading_copy": [
        "Kaelra is checking your day…",
        "Syncing your accounts…",
        "Preparing actions for your approval…"
      ],
      "skeleton": "Use shadcn Skeleton with rounded-[14px] and subtle shimmer (via bg-white/5).",
      "data_testid": {
        "loading": "kaelra-loading-state",
        "empty": "kaelra-empty-state"
      }
    }
  },

  "motion": {
    "library": {
      "recommended": "framer-motion",
      "why": "Entrance animations, layout transitions, orb state changes without janky CSS.",
      "install": "npm i framer-motion",
      "usage_notes": [
        "Use motion.div for card entrance (y: 8→0, opacity: 0→1, duration 0.35)",
        "Use layoutId for smooth transitions between Today orb and Talk orb",
        "Respect prefers-reduced-motion"
      ]
    },
    "micro_interactions": [
      "Buttons: hover brighten + slight lift (translateY(-1px)) and active press (scale 0.98)",
      "Cards: hover border highlight + subtle background increase (glass strong)",
      "Command bar: focus expands glow ring (box-shadow token)",
      "Queue items: approve triggers success toast + badge morph"
    ],
    "transition_rule": "Never use transition: all. Use transition-colors, transition-shadow, transition-opacity only."
  },

  "data_viz": {
    "charts": {
      "library": "recharts",
      "install": "npm i recharts",
      "use_cases": [
        "Goals progress mini area chart",
        "Weekly focus time bar chart",
        "Email volume sparkline"
      ],
      "styling": {
        "grid": "stroke='rgba(255,255,255,0.08)'",
        "line": "stroke='#2DD4BF' strokeWidth={2}",
        "tooltip": "Use shadcn Tooltip/Popover with glass recipe"
      }
    }
  },

  "accessibility": {
    "contrast": [
      "Never place dark text on translucent dark surfaces.",
      "Muted text must remain readable: target ~70% lightness equivalent on dark."
    ],
    "focus": [
      "All interactive elements must have visible focus ring (ring color = teal).",
      "Use focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-0"
    ],
    "reduced_motion": [
      "Disable orb animations and heavy entrance transitions when prefers-reduced-motion is set.",
      "Keep state changes via opacity only."
    ],
    "touch_targets": "Minimum 44px height for primary controls (command bar, approve/reject)."
  },

  "image_urls": {
    "background_textures": [
      {
        "category": "app-shell-background",
        "description": "Dark abstract teal glass texture for subtle background layer (use with low opacity, blur).",
        "url": "https://images.unsplash.com/photo-1708305729900-906f34a7d49d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzZ8MHwxfHNlYXJjaHwxfHxkYXJrJTIwYWJzdHJhY3QlMjBnbGFzcyUyMGdyYWRpZW50JTIwdGV4dHVyZXxlbnwwfHx8dGVhbHwxNzgyMDk2MTYyfDA&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "app-shell-background",
        "description": "Raindrop glass texture for noise-like depth (use as overlay at 4–6% opacity).",
        "url": "https://images.pexels.com/photos/9807251/pexels-photo-9807251.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
      }
    ],
    "optional_context_images": [
      {
        "category": "onboarding-side-panel (desktop only)",
        "description": "Premium dark workspace photo for onboarding ambience (keep subtle, heavily darkened).",
        "url": "https://images.unsplash.com/photo-1577384913373-015cbc659e27?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAxODF8MHwxfHNlYXJjaHwxfHxmdXR1cmlzdGljJTIwZGFyayUyMHdvcmtzcGFjZSUyMGRlc2slMjBsYXB0b3AlMjBuaWdodHxlbnwwfHx8Ymx1ZXwxNzgyMDk2MTY2fDA&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "page_level_guidance": {
    "auth": {
      "layout": "Split layout on desktop: left = form glass card, right = ambient image + orb. Mobile = single column.",
      "primary_action": "Sign in",
      "secondary": "Demo login",
      "data_testid": [
        "auth-email-input",
        "auth-password-input",
        "auth-submit-button",
        "auth-demo-login-button"
      ]
    },
    "onboarding": {
      "pattern": "Multi-step wizard using Tabs or custom stepper; each step is a glass card with 1 primary action.",
      "components": ["progress", "select", "switch", "calendar"],
      "data_testid": [
        "onboarding-next-button",
        "onboarding-back-button",
        "onboarding-step-title"
      ]
    },
    "today": {
      "pattern": "Command center grid + featured orb + daily briefing hero card.",
      "data_testid": [
        "today-daily-briefing-card",
        "today-action-queue-preview",
        "today-device-sync-status"
      ]
    },
    "talk": {
      "pattern": "Orb-centered conversation with side history on desktop; mobile uses Drawer for history.",
      "components": ["scroll-area", "drawer", "tabs"],
      "voice_button": "Use Button size=icon with mic icon; show listening state via orb.",
      "data_testid": [
        "talk-message-list",
        "talk-composer-input",
        "talk-send-button",
        "talk-voice-button"
      ]
    },
    "queue": {
      "pattern": "Filter tabs (Pending/Approved/Snoozed) + list of action cards.",
      "components": ["tabs", "badge", "dialog"],
      "data_testid": [
        "queue-filter-tabs",
        "queue-action-card"
      ]
    },
    "memory": {
      "pattern": "Category chips + card grid; edit in Dialog; 'Forget' is destructive with AlertDialog.",
      "components": ["alert-dialog", "dialog", "badge"],
      "data_testid": [
        "memory-category-filter",
        "memory-add-button",
        "memory-forget-button"
      ]
    },
    "connected_accounts": {
      "pattern": "Integration cards with state badges and connect CTA.",
      "components": ["card", "badge", "button"],
      "data_testid": [
        "integration-card",
        "integration-connect-button"
      ]
    },
    "settings_privacy": {
      "pattern": "Two-column settings on desktop; accordion sections on mobile.",
      "components": ["accordion", "switch", "select", "alert-dialog"],
      "data_testid": [
        "settings-tone-select",
        "settings-export-data-button",
        "settings-delete-data-button"
      ]
    }
  },

  "instructions_to_main_agent": [
    "Set the app to dark mode by default (apply .dark on html/body or root wrapper).",
    "Replace the default shadcn tokens in /app/frontend/src/index.css with the Kaelra dark-first HSL tokens above.",
    "Do NOT keep App.css centered header styles; remove/ignore .App-header centering patterns.",
    "Implement a persistent shell: desktop sidebar + mobile tab bar; keep a small Kaelra orb + global status line always visible.",
    "Use shadcn Command component to build the global command bar; it must be present on every logged-in screen.",
    "All interactive and key informational elements must include stable data-testid attributes (kebab-case).",
    "Use glass card recipe for all dashboard modules; keep gradients decorative only (<=20% viewport).",
    "Add Framer Motion for subtle entrance + orb state transitions; respect prefers-reduced-motion.",
    "Use Sonner for toasts (approval/rejection/sync events)."
  ]
}

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
   • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>

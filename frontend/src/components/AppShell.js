import React, { useCallback, useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutGrid, MessageCircle, ListChecks, Brain, FolderOpen,
  Bell, Plug, MonitorSmartphone, Settings as SettingsIcon,
  Menu, LogOut, ChevronRight, Briefcase, GraduationCap, Rocket, Home, Sparkles,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { KaelraOrb } from "./KaelraOrb";
import { CommandBar } from "./CommandBar";
import { Sheet, SheetContent, SheetTrigger } from "./ui/sheet";
import { Button } from "./ui/button";

const PRIMARY_NAV = [
  { to: "/", label: "Kaelra", icon: Sparkles, end: true },
  { to: "/queue", label: "Action Queue", icon: ListChecks, badgeKey: "pending" },
  { to: "/memory", label: "Memory", icon: Brain },
  { to: "/files", label: "Files", icon: FolderOpen },
];
const ALL_SKILLS = {
  jobs: { to: "/jobs", label: "Jobs & Career", icon: Briefcase },
  class: { to: "/class", label: "Class & School", icon: GraduationCap },
  founder: { to: "/founder", label: "Founder Workspace", icon: Rocket },
  home: { to: "/home", label: "Smart Home", icon: Home },
};
const SKILL_ORDER = ["jobs", "class", "founder", "home"];
const CONTROL_NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/routines", label: "Routines", icon: Bell },
  { to: "/accounts", label: "Connected Accounts", icon: Plug },
  { to: "/devices", label: "Devices", icon: MonitorSmartphone },
  { to: "/settings", label: "Settings & Privacy", icon: SettingsIcon },
];
const MOBILE_TABS = [
  { to: "/", label: "Kaelra", icon: Sparkles, end: true },
  { to: "/queue", label: "Queue", icon: ListChecks, badgeKey: "pending" },
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
];

// ---- Lightweight cross-screen status sync ----
export function triggerKaelraRefresh() {
  window.dispatchEvent(new Event("kaelra-refresh"));
}

function NavItem({ item, counts, onClick }) {
  const badge = item.badgeKey ? counts[item.badgeKey] : 0;
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onClick}
      data-testid="app-nav-item"
      className={({ isActive }) =>
        `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors ${
          isActive
            ? "bg-white/10 border border-white/10 text-foreground"
            : "text-muted-foreground hover:text-foreground hover:bg-white/5 border border-transparent"
        }`
      }
    >
      <item.icon size={18} className="shrink-0" />
      <span className="flex-1 truncate">{item.label}</span>
      {badge > 0 && (
        <span className="ml-auto inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-[hsl(var(--primary))] px-1.5 text-[11px] font-semibold text-[hsl(var(--primary-foreground))]">
          {badge}
        </span>
      )}
    </NavLink>
  );
}

export function AppShell({ children, title }) {
  const { user, profile, logout } = useAuth();
  const [counts, setCounts] = useState({ pending: 0 });
  const [relevantSkills, setRelevantSkills] = useState([]);
  const [showAllSkills, setShowAllSkills] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/actions", { params: { status: "pending" } });
      setCounts({ pending: data.length });
    } catch (e) { /* ignore */ }
    try {
      const { data } = await api.get("/skills/relevant");
      setRelevantSkills((data.skills || []).map((s) => s.key));
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => { refresh(); }, [refresh, location.pathname]);
  useEffect(() => {
    const h = () => refresh();
    window.addEventListener("kaelra-refresh", h);
    const t = setInterval(refresh, 30000);
    return () => { window.removeEventListener("kaelra-refresh", h); clearInterval(t); };
  }, [refresh]);

  const name = profile?.call_me || user?.name || "there";
  const skillKeys = showAllSkills ? SKILL_ORDER : relevantSkills.filter((k) => ALL_SKILLS[k]);
  const skillItems = skillKeys.map((k) => ALL_SKILLS[k]).filter(Boolean);
  const hasHiddenSkills = relevantSkills.length < SKILL_ORDER.length;

  return (
    <div className="kaelra-app-bg min-h-screen text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-[1500px]">
        {/* Desktop sidebar */}
        <aside className="hidden lg:flex w-[286px] xl:w-[300px] shrink-0 flex-col gap-2 border-r border-white/10 bg-[var(--kaelra-glass)] backdrop-blur-md p-4">
          <button onClick={() => navigate("/")} className="flex items-center gap-3 px-2 py-3 text-left">
            <KaelraOrb size={40} state="idle" />
            <div>
              <div className="font-heading text-lg leading-none">Kaelra</div>
              <div className="kaelra-kicker mt-1">Personal Operator</div>
            </div>
          </button>

          <nav className="mt-2 flex flex-1 min-h-0 flex-col gap-1 overflow-y-auto pr-1">
            {PRIMARY_NAV.map((item) => <NavItem key={item.to} item={item} counts={counts} />)}

            {(skillItems.length > 0 || hasHiddenSkills) && (
              <div className="px-3 pb-1 pt-3 kaelra-kicker">Skills</div>
            )}
            {skillItems.map((item) => <NavItem key={item.to} item={item} counts={counts} />)}
            {hasHiddenSkills && (
              <button onClick={() => setShowAllSkills((v) => !v)} data-testid="nav-toggle-skills"
                className="flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground">
                <ChevronRight size={14} className={`transition-transform ${showAllSkills ? "rotate-90" : ""}`} />
                {showAllSkills ? "Show fewer" : "Explore all skills"}
              </button>
            )}

            <div className="my-2 h-px bg-white/5" />
            <div className="px-3 pb-1 kaelra-kicker">Control panel</div>
            {CONTROL_NAV.map((item) => <NavItem key={item.to} item={item} counts={counts} />)}
          </nav>

          <div className="mt-auto">
            <div className="glass rounded-xl p-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="h-2 w-2 rounded-full bg-[hsl(var(--primary))] animate-pulse" />
                <span className="font-mono-k">Synced on this device</span>
              </div>
              <div className="mt-2 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate text-sm">{name}</div>
                  <div className="truncate text-xs text-muted-foreground">{user?.email}</div>
                </div>
                <Button data-testid="app-logout-button" size="icon" variant="ghost" onClick={logout} aria-label="Log out">
                  <LogOut size={16} />
                </Button>
              </div>
            </div>
          </div>
        </aside>

        {/* Main column */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Top bar */}
          <header className="sticky top-0 z-30 border-b border-white/10 bg-[rgba(11,15,20,0.72)] backdrop-blur-md">
            <div className="flex items-center gap-3 px-4 py-3 md:px-6">
              {/* Mobile presence */}
              <div className="flex items-center gap-2 lg:hidden">
                <KaelraOrb size={34} state="idle" />
              </div>
              <div className="hidden lg:block min-w-[120px]">
                <div className="kaelra-kicker">Kaelra</div>
                <div className="font-heading text-lg leading-none">{title || "Kaelra"}</div>
              </div>
              <div className="mx-auto w-full max-w-xl">
                <CommandBar compact />
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Menu"
                  onClick={() => setMoreOpen(true)} data-testid="mobile-menu-button">
                  <Menu size={20} />
                </Button>
              </div>
            </div>
          </header>

          <main className="flex-1 px-4 pb-28 pt-5 md:px-6 lg:pb-8">{children}</main>
        </div>
      </div>

      {/* Mobile bottom tab bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-[10000] flex items-stretch border-t border-white/10 bg-[rgba(15,22,32,0.92)] backdrop-blur-md pb-[env(safe-area-inset-bottom)] lg:hidden">
        {MOBILE_TABS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            data-testid="mobile-tabbar-item"
            className={({ isActive }) =>
              `relative flex flex-1 flex-col items-center justify-center gap-1 py-2.5 text-[11px] ${
                isActive ? "text-[hsl(var(--primary))]" : "text-muted-foreground"
              }`
            }
          >
            <item.icon size={20} />
            <span>{item.label.split(" ")[0]}</span>
            {item.badgeKey && counts[item.badgeKey] > 0 && (
              <span className="absolute right-[22%] top-1 h-4 min-w-4 rounded-full bg-[hsl(var(--primary))] px-1 text-[10px] font-semibold leading-4 text-[hsl(var(--primary-foreground))]">
                {counts[item.badgeKey]}
              </span>
            )}
          </NavLink>
        ))}
        <button
          onClick={() => setMoreOpen(true)}
          data-testid="mobile-tabbar-more"
          className="flex flex-1 flex-col items-center justify-center gap-1 py-2.5 text-[11px] text-muted-foreground"
        >
          <Menu size={20} />
          <span>More</span>
        </button>
      </nav>

      {/* Mobile "more" sheet */}
      <Sheet open={moreOpen} onOpenChange={setMoreOpen}>
        <SheetContent side="right" className="w-[290px] border-white/10 bg-[rgba(15,22,32,0.96)] backdrop-blur-xl">
          <div className="flex items-center gap-3 pb-4">
            <KaelraOrb size={36} />
            <div>
              <div className="font-heading">Kaelra</div>
              <div className="text-xs text-muted-foreground">{name}</div>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            {[...PRIMARY_NAV, ...SKILL_ORDER.map((k) => ALL_SKILLS[k]), ...CONTROL_NAV].map((item) => (
              <NavItem key={item.to} item={item} counts={counts} onClick={() => setMoreOpen(false)} />
            ))}
          </div>
          <button
            onClick={logout}
            data-testid="app-logout-button-mobile"
            className="mt-4 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted-foreground hover:bg-white/5"
          >
            <LogOut size={18} /> <span className="flex-1 text-left">Log out</span>
            <ChevronRight size={16} />
          </button>
        </SheetContent>
      </Sheet>
    </div>
  );
}

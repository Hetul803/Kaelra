import {
  Mail, Bell, Car, Newspaper, FileText, FolderInput, Briefcase, FilePlus2,
  CalendarClock, CalendarPlus, CornerUpRight, Rocket, CheckSquare, AlarmClock, MailPlus,
  Bookmark, Paperclip, BookOpen, Share2, ListTodo, BarChart3, TrendingUp, Users,
  Lightbulb, Thermometer, Repeat, Lock, Sunrise,
} from "lucide-react";

export const ACTION_META = {
  draft_email: { icon: MailPlus, label: "Draft email" },
  summarize_email: { icon: Mail, label: "Summarize email" },
  create_reminder: { icon: Bell, label: "Reminder" },
  schedule_alarm_placeholder: { icon: AlarmClock, label: "Alarm" },
  commute_alert: { icon: Car, label: "Commute" },
  news_brief: { icon: Newspaper, label: "News" },
  file_summary: { icon: FileText, label: "File summary" },
  organize_file_suggestion: { icon: FolderInput, label: "Organize files" },
  job_match: { icon: Briefcase, label: "Job match" },
  draft_application: { icon: FilePlus2, label: "Application" },
  assignment_reminder: { icon: CalendarClock, label: "Assignment" },
  calendar_suggestion: { icon: CalendarPlus, label: "Calendar" },
  follow_up: { icon: CornerUpRight, label: "Follow-up" },
  startup_task: { icon: Rocket, label: "Startup" },
  general_task: { icon: CheckSquare, label: "Task" },
  // Jobs / Career
  save_job: { icon: Bookmark, label: "Save job" },
  draft_recruiter_reply: { icon: MailPlus, label: "Recruiter reply" },
  attach_resume: { icon: Paperclip, label: "Attach resume" },
  create_follow_up: { icon: CornerUpRight, label: "Follow-up" },
  mark_applied: { icon: CheckSquare, label: "Applied" },
  prepare_application: { icon: FilePlus2, label: "Application" },
  // Class / School
  study_plan: { icon: BookOpen, label: "Study plan" },
  professor_reply_draft: { icon: Mail, label: "Professor reply" },
  deadline_alert: { icon: CalendarClock, label: "Deadline" },
  // Founder
  draft_linkedin_post: { icon: Share2, label: "LinkedIn post" },
  create_product_task: { icon: ListTodo, label: "Product task" },
  summarize_metrics: { icon: BarChart3, label: "Metrics" },
  suggest_growth_action: { icon: TrendingUp, label: "Growth move" },
  follow_up_user: { icon: Users, label: "Follow up" },
  // Smart Home
  turn_light_on: { icon: Lightbulb, label: "Light" },
  set_temperature: { icon: Thermometer, label: "Thermostat" },
  create_home_routine: { icon: Repeat, label: "Home routine" },
  lock_door_pending_approval: { icon: Lock, label: "Lock" },
  morning_home_routine: { icon: Sunrise, label: "Home routine" },
};

export function actionMeta(type) {
  return ACTION_META[type] || ACTION_META.general_task;
}

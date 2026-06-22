import {
  Mail, Bell, Car, Newspaper, FileText, FolderInput, Briefcase, FilePlus2,
  CalendarClock, CalendarPlus, CornerUpRight, Rocket, CheckSquare, AlarmClock, MailPlus,
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
};

export function actionMeta(type) {
  return ACTION_META[type] || ACTION_META.general_task;
}

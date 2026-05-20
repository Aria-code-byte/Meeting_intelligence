/**
 * Core data models for Jinni AI
 * These types define the structure of all persistent data
 */

export type MeetingStatus =
  | 'uploaded'
  | 'transcribing'
  | 'summarizing'
  | 'completed'
  | 'failed';

export interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  participants: string[];
  status: MeetingStatus;
  progress?: number;
  templateId?: string;
  audioFileName?: string;
  audioFileUrl?: string;
  transcript?: string;
  summary?: string;
  actionItemIds?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface SummaryTemplate {
  id: string;
  name: string;
  description: string;
  type: 'built-in' | 'custom';
  category?: string;
  tags: string[];
  prompt?: string;
  structure?: string[];
  isDefault: boolean;
  isBuiltIn: boolean;
  createdAt: string;
  updatedAt: string;
}

export type ActionItemStatus = 'todo' | 'in_progress' | 'done';

export interface ActionItem {
  id: string;
  meetingId: string;
  content: string;
  owner?: string;
  dueDate?: string;
  status: ActionItemStatus;
  createdAt: string;
  updatedAt: string;
}

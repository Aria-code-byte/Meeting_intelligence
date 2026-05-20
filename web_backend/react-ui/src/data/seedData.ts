/**
 * Seed data for initial application state
 * This data is loaded only when localStorage is empty
 */

import type { Meeting, SummaryTemplate, ActionItem } from '../types/models';

export const seedMeetings: Meeting[] = [
  {
    id: '1',
    title: 'Q3 Product Strategy Sync',
    date: '2024-10-24',
    duration: '45m',
    participants: ['Alice', 'Bob', 'Charlie'],
    status: 'completed',
    progress: 100,
    templateId: '1',
    createdAt: '2024-10-24T10:00:00Z',
    updatedAt: '2024-10-24T10:45:00Z',
  },
  {
    id: '2',
    title: 'Interview: Senior Designer',
    date: '2024-10-25',
    duration: '1h 12m',
    participants: ['David', 'Eve'],
    status: 'processing',
    progress: 68,
    templateId: '3',
    createdAt: '2024-10-25T14:00:00Z',
    updatedAt: '2024-10-25T14:48:00Z',
  },
  {
    id: '3',
    title: 'Marketing Campaign Kickoff',
    date: '2024-10-22',
    duration: '30m',
    participants: ['Frank', 'Grace', 'Heidi'],
    status: 'completed',
    progress: 100,
    templateId: '1',
    createdAt: '2024-10-22T09:00:00Z',
    updatedAt: '2024-10-22T09:30:00Z',
  },
];

export const seedTemplates: SummaryTemplate[] = [
  {
    id: '1',
    name: '通用会议模板',
    description: '适用于大多数商务会议，包含会议概要、关键决策和行动项',
    type: 'built-in',
    category: 'general',
    tags: ['通用', '商务'],
    isDefault: true,
    isBuiltIn: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: '技术评审模板',
    description: '专注于技术讨论和决策，包含技术细节和实施计划',
    type: 'built-in',
    category: 'technical',
    tags: ['技术', '开发'],
    isDefault: false,
    isBuiltIn: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: '3',
    name: '面试记录模板',
    description: '用于面试记录和评估，包含候选人信息和评分',
    type: 'built-in',
    category: 'interview',
    tags: ['HR', '面试'],
    isDefault: false,
    isBuiltIn: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

export const seedActionItems: ActionItem[] = [
  {
    id: '1',
    meetingId: '1',
    content: '完成 Glassmorphism 设计规范文档',
    owner: 'Alice Chen',
    dueDate: '2024-10-30',
    status: 'todo',
    createdAt: '2024-10-24T10:45:00Z',
    updatedAt: '2024-10-24T10:45:00Z',
  },
  {
    id: '2',
    meetingId: '1',
    content: '评估移动端 BottomNavBar 性能影响',
    owner: 'Bob Wang',
    dueDate: '2024-11-01',
    status: 'in_progress',
    createdAt: '2024-10-24T10:45:00Z',
    updatedAt: '2024-10-24T10:45:00Z',
  },
  {
    id: '3',
    meetingId: '1',
    content: '整理当前页面用户停留时间数据',
    owner: 'Charlie Liu',
    dueDate: '2024-10-27',
    status: 'done',
    createdAt: '2024-10-24T10:45:00Z',
    updatedAt: '2024-10-24T10:45:00Z',
  },
];

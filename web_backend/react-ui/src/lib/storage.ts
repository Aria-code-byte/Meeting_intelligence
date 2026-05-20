/**
 * LocalStorage wrapper for data persistence
 * Provides type-safe CRUD operations with localStorage backend
 */

import type { Meeting, SummaryTemplate, ActionItem } from '../types/models';
import { seedMeetings, seedTemplates, seedActionItems } from '../data/seedData';

// localStorage keys
const STORAGE_KEYS = {
  MEETINGS: 'jinni_meetings',
  TEMPLATES: 'jinni_templates',
  ACTION_ITEMS: 'jinni_action_items',
} as const;

// Generic storage helpers
function getFromStorage<T>(key: string, defaultValue: T[]): T[] {
  try {
    const item = localStorage.getItem(key);
    if (!item) return defaultValue;
    const parsed = JSON.parse(item);
    return Array.isArray(parsed) ? parsed : defaultValue;
  } catch (error) {
    console.error(`Error reading from localStorage key "${key}":`, error);
    return defaultValue;
  }
}

function saveToStorage<T>(key: string, data: T[]): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(data));
    return true;
  } catch (error) {
    console.error(`Error writing to localStorage key "${key}":`, error);
    return false;
  }
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Initialize seed data if storage is empty
function initializeSeedData() {
  if (!localStorage.getItem(STORAGE_KEYS.MEETINGS)) {
    saveToStorage(STORAGE_KEYS.MEETINGS, seedMeetings);
  }
  if (!localStorage.getItem(STORAGE_KEYS.TEMPLATES)) {
    saveToStorage(STORAGE_KEYS.TEMPLATES, seedTemplates);
  }
  if (!localStorage.getItem(STORAGE_KEYS.ACTION_ITEMS)) {
    saveToStorage(STORAGE_KEYS.ACTION_ITEMS, seedActionItems);
  }
}

// Initialize on module load
initializeSeedData();

// Meeting storage operations
export const meetingStorage = {
  getAll: (): Meeting[] => {
    return getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
  },

  getById: (id: string): Meeting | null => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    return meetings.find(m => m.id === id) || null;
  },

  create: (data: Omit<Meeting, 'id' | 'createdAt' | 'updatedAt'>): Meeting => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const now = new Date().toISOString();
    const newMeeting: Meeting = {
      ...data,
      id: generateId(),
      createdAt: now,
      updatedAt: now,
    };
    saveToStorage(STORAGE_KEYS.MEETINGS, [...meetings, newMeeting]);
    return newMeeting;
  },

  update: (id: string, patch: Partial<Omit<Meeting, 'id' | 'createdAt'>>): Meeting | null => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const index = meetings.findIndex(m => m.id === id);
    if (index === -1) return null;

    const updatedMeeting: Meeting = {
      ...meetings[index],
      ...patch,
      id,
      createdAt: meetings[index].createdAt,
      updatedAt: new Date().toISOString(),
    };

    meetings[index] = updatedMeeting;
    saveToStorage(STORAGE_KEYS.MEETINGS, meetings);
    return updatedMeeting;
  },

  delete: (id: string): boolean => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const filtered = meetings.filter(m => m.id !== id);
    if (filtered.length === meetings.length) return false;
    saveToStorage(STORAGE_KEYS.MEETINGS, filtered);
    return true;
  },

  getRecent: (limit: number = 5): Meeting[] => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    return meetings
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, limit);
  },
};

// Template storage operations
export const templateStorage = {
  getAll: (): SummaryTemplate[] => {
    return getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
  },

  getById: (id: string): SummaryTemplate | null => {
    const templates = getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
    return templates.find(t => t.id === id) || null;
  },

  create: (data: Omit<SummaryTemplate, 'id' | 'createdAt' | 'updatedAt'>): SummaryTemplate => {
    const templates = getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
    const now = new Date().toISOString();
    const newTemplate: SummaryTemplate = {
      ...data,
      id: generateId(),
      createdAt: now,
      updatedAt: now,
    };

    // If this is the default template, clear default from others
    if (newTemplate.isDefault) {
      templates.forEach(t => t.isDefault = false);
    }

    saveToStorage(STORAGE_KEYS.TEMPLATES, [...templates, newTemplate]);
    return newTemplate;
  },

  update: (id: string, patch: Partial<Omit<SummaryTemplate, 'id' | 'createdAt'>>): SummaryTemplate | null => {
    const templates = getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
    const index = templates.findIndex(t => t.id === id);
    if (index === -1) return null;

    // If setting as default, clear default from others
    if (patch.isDefault && !templates[index].isDefault) {
      templates.forEach(t => t.isDefault = false);
    }

    const updatedTemplate: SummaryTemplate = {
      ...templates[index],
      ...patch,
      id,
      createdAt: templates[index].createdAt,
      updatedAt: new Date().toISOString(),
    };

    templates[index] = updatedTemplate;
    saveToStorage(STORAGE_KEYS.TEMPLATES, templates);
    return updatedTemplate;
  },

  delete: (id: string): boolean => {
    const templates = getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
    const template = templates.find(t => t.id === id);

    // Prevent deletion of built-in templates
    if (template?.isBuiltIn) return false;

    const filtered = templates.filter(t => t.id !== id);
    if (filtered.length === templates.length) return false;

    saveToStorage(STORAGE_KEYS.TEMPLATES, filtered);
    return true;
  },

  setDefault: (id: string): boolean => {
    const templates = getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
    const template = templates.find(t => t.id === id);
    if (!template) return false;

    templates.forEach(t => t.isDefault = false);
    template.isDefault = true;

    saveToStorage(STORAGE_KEYS.TEMPLATES, templates);
    return true;
  },

  getDefault: (): SummaryTemplate | null => {
    const templates = getFromStorage<SummaryTemplate>(STORAGE_KEYS.TEMPLATES, []);
    return templates.find(t => t.isDefault) || null;
  },
};

// ActionItem storage operations
export const actionItemStorage = {
  getAll: (): ActionItem[] => {
    return getFromStorage<ActionItem>(STORAGE_KEYS.ACTION_ITEMS, []);
  },

  getByMeetingId: (meetingId: string): ActionItem[] => {
    const items = getFromStorage<ActionItem>(STORAGE_KEYS.ACTION_ITEMS, []);
    return items.filter(item => item.meetingId === meetingId);
  },

  create: (data: Omit<ActionItem, 'id' | 'createdAt' | 'updatedAt'>): ActionItem => {
    const items = getFromStorage<ActionItem>(STORAGE_KEYS.ACTION_ITEMS, []);
    const now = new Date().toISOString();
    const newItem: ActionItem = {
      ...data,
      id: generateId(),
      createdAt: now,
      updatedAt: now,
    };
    saveToStorage(STORAGE_KEYS.ACTION_ITEMS, [...items, newItem]);

    // Update meeting's actionItemIds
    if (data.meetingId) {
      const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
      const meeting = meetings.find(m => m.id === data.meetingId);
      if (meeting) {
        const currentIds = meeting.actionItemIds || [];
        meetingStorage.update(data.meetingId, {
          actionItemIds: [...currentIds, newItem.id],
        });
      }
    }

    return newItem;
  },

  update: (id: string, patch: Partial<Omit<ActionItem, 'id' | 'createdAt'>>): ActionItem | null => {
    const items = getFromStorage<ActionItem>(STORAGE_KEYS.ACTION_ITEMS, []);
    const index = items.findIndex(item => item.id === id);
    if (index === -1) return null;

    const updatedItem: ActionItem = {
      ...items[index],
      ...patch,
      id,
      createdAt: items[index].createdAt,
      updatedAt: new Date().toISOString(),
    };

    items[index] = updatedItem;
    saveToStorage(STORAGE_KEYS.ACTION_ITEMS, items);
    return updatedItem;
  },

  delete: (id: string): boolean => {
    const items = getFromStorage<ActionItem>(STORAGE_KEYS.ACTION_ITEMS, []);
    const filtered = items.filter(item => item.id !== id);
    if (filtered.length === items.length) return false;

    // Remove from meeting's actionItemIds
    const deletedItem = items.find(i => i.id === id);
    if (deletedItem?.meetingId) {
      const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
      const meeting = meetings.find(m => m.id === deletedItem.meetingId);
      if (meeting?.actionItemIds) {
        meetingStorage.update(deletedItem.meetingId, {
          actionItemIds: meeting.actionItemIds.filter(itemId => itemId !== id),
        });
      }
    }

    saveToStorage(STORAGE_KEYS.ACTION_ITEMS, filtered);
    return true;
  },
};

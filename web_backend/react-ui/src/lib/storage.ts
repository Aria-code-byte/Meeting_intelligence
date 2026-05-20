/**
 * LocalStorage wrapper for data persistence
 * Provides type-safe CRUD operations with localStorage backend
 */

import type { Meeting, SummaryTemplate, ActionItem } from '../types/models';
import { seedMeetings, seedTemplates, seedActionItems } from '../data/seedData';
import { generateId, isLegacyTimestampId } from './id';

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
    return defaultValue;
  }
}

function saveToStorage<T>(key: string, data: T[]): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(data));
    return true;
  } catch (error) {
    return false;
  }
}

// Use the unified ID generator from id.ts
// This function is kept for backward compatibility but now uses the new implementation
function generateStorageId(prefix?: string): string {
  return generateId(prefix);
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

/**
 * Normalize meetings - fix duplicate IDs and remove obvious duplicates
 * This handles cases where:
 * 1. Multiple records have the same ID (from old Date.now() generation)
 * 2. Multiple records have identical content (true duplicates)
 *
 * Returns [normalizedMeetings, hasChanges] tuple
 */
function normalizeMeetings(meetings: Meeting[]): [Meeting[], boolean] {
  const seenIds = new Set<string>();
  const seenContent = new Set<string>();
  const normalized: Meeting[] = [];
  let regeneratedIds = 0;
  let removedDuplicates = 0;

  for (const meeting of meetings) {
    let normalizedMeeting = { ...meeting };

    // Check 1: Fix duplicate or legacy IDs
    if (!normalizedMeeting.id || seenIds.has(normalizedMeeting.id) || isLegacyTimestampId(normalizedMeeting.id)) {
      const oldId = normalizedMeeting.id;
      normalizedMeeting.id = generateStorageId('meeting');
      normalizedMeeting.updatedAt = new Date().toISOString();
      regeneratedIds++;
    }

    // Check 2: Detect content duplicates (title + date + duration + participants)
    // Only if this looks like an actual duplicate, not just similar meetings
    const contentKey = `${normalizedMeeting.title}|${normalizedMeeting.date}|${normalizedMeeting.duration}|${normalizedMeeting.participants.sort().join(',')}`;

    if (seenContent.has(contentKey)) {
      // This is a true duplicate, skip it
      removedDuplicates++;
      continue;
    }

    seenIds.add(normalizedMeeting.id);
    seenContent.add(contentKey);
    normalized.push(normalizedMeeting);
  }


  // Return both normalized meetings and a flag indicating if changes were made
  return [normalized, regeneratedIds > 0 || removedDuplicates > 0];
}

// Run normalization on module load to fix existing data
function runInitialNormalization() {
  const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
  if (meetings.length > 0) {
    const [normalized, hasChanges] = normalizeMeetings(meetings);
    if (hasChanges) {
      saveToStorage(STORAGE_KEYS.MEETINGS, normalized);
    }
  }
}

// Run normalization on module load
runInitialNormalization();

// Meeting storage operations
export const meetingStorage = {
  getAll: (): Meeting[] => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    // Always normalize to ensure unique IDs
    const [normalized, hasChanges] = normalizeMeetings(meetings);

    // If normalization made changes, write back to localStorage immediately
    if (hasChanges) {
      saveToStorage(STORAGE_KEYS.MEETINGS, normalized);
    }

    return normalized;
  },

  getById: (id: string): Meeting | null => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const [normalized] = normalizeMeetings(meetings);
    return normalized.find(m => m.id === id) || null;
  },

  create: (data: Omit<Meeting, 'id' | 'createdAt' | 'updatedAt'>): Meeting => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const now = new Date().toISOString();
    const newMeeting: Meeting = {
      ...data,
      id: generateStorageId('meeting'),
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
    // First normalize to ensure we're working with clean data
    // Read raw data and normalize it
    const rawMeetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const [meetings, hasChanges] = normalizeMeetings(rawMeetings);

    // If normalization made changes, save the normalized version first
    if (hasChanges) {
      saveToStorage(STORAGE_KEYS.MEETINGS, meetings);
    }

    const index = meetings.findIndex(m => m.id === id);

    if (index === -1) {
      return false;
    }

    meetings.splice(index, 1);
    const success = saveToStorage(STORAGE_KEYS.MEETINGS, meetings);

    return success;
  },

  getRecent: (limit: number = 5): Meeting[] => {
    const meetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    return meetings
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, limit);
  },

  /**
   * Force repair all meeting data in localStorage
   * This fixes duplicate IDs, legacy timestamp IDs, and obvious duplicate records
   * Can be called manually during development or after data migrations
   */
  repair: (): { before: number; after: number; repaired: boolean; details: string[] } => {
    const rawMeetings = getFromStorage<Meeting>(STORAGE_KEYS.MEETINGS, []);
    const [normalized, hasChanges] = normalizeMeetings(rawMeetings);

    const details: string[] = [];

    if (hasChanges) {
      // Find what changed
      const rawIds = rawMeetings.map(m => m.id);
      const normalizedIds = normalized.map(m => m.id);
      const duplicateIds = rawIds.filter((id, index) => rawIds.indexOf(id) !== index);

      if (duplicateIds.length > 0) {
        details.push(`Fixed ${duplicateIds.length} duplicate IDs: ${duplicateIds.join(', ')}`);
      }

      if (rawMeetings.length !== normalized.length) {
        details.push(`Removed ${rawMeetings.length - normalized.length} duplicate records`);
      }

      saveToStorage(STORAGE_KEYS.MEETINGS, normalized);
    }

    // Verify no duplicates remain
    const finalIds = normalized.map(m => m.id);
    const uniqueIds = new Set(finalIds);
    const hasDuplicates = finalIds.length !== uniqueIds.size;


    return {
      before: rawMeetings.length,
      after: normalized.length,
      repaired: hasChanges,
      details,
    };
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
      id: generateStorageId('template'),
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
      id: generateStorageId('action'),
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

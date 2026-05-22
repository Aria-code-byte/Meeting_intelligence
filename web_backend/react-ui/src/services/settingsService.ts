/**
 * User settings service
 * Manages user preferences stored in localStorage
 */

import type { ExportFormat } from './exportService';

const STORAGE_KEY = 'jinni_user_settings';

export interface UserSettings {
  displayName: string;
  defaultTemplateId?: string;
  exportFormatPreference: ExportFormat;
  includeTranscriptByDefault: boolean;
  updatedAt: string;
}

const DEFAULT_SETTINGS: UserSettings = {
  displayName: '本地用户',
  exportFormatPreference: 'markdown',
  includeTranscriptByDefault: true,
  updatedAt: new Date().toISOString(),
};

/**
 * Get user settings from localStorage
 */
export function getUserSettings(): UserSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return { ...DEFAULT_SETTINGS, ...parsed };
    }
  } catch (error) {
    console.error('Failed to load user settings:', error);
  }
  return { ...DEFAULT_SETTINGS };
}

/**
 * Save user settings to localStorage
 */
export function saveUserSettings(settings: Partial<UserSettings>): UserSettings {
  const current = getUserSettings();
  const updated: UserSettings = {
    ...current,
    ...settings,
    updatedAt: new Date().toISOString(),
  };

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Failed to save user settings:', error);
  }

  return updated;
}

/**
 * Update display name
 */
export function updateDisplayName(displayName: string): UserSettings {
  return saveUserSettings({ displayName: displayName.trim() || '本地用户' });
}

/**
 * Update default template
 */
export function updateDefaultTemplate(templateId: string | undefined): UserSettings {
  return saveUserSettings({ defaultTemplateId: templateId });
}

/**
 * Update export format preference
 */
export function updateExportFormatPreference(format: ExportFormat): UserSettings {
  return saveUserSettings({ exportFormatPreference: format });
}

/**
 * Update include transcript by default
 */
export function updateIncludeTranscriptByDefault(include: boolean): UserSettings {
  return saveUserSettings({ includeTranscriptByDefault: include });
}

/**
 * Clear all local data
 */
export function clearAllLocalData(): void {
  const keys = [
    'jinni_meetings',
    'jinni_templates',
    'jinni_action_items',
    'jinni_user_settings',
  ];

  keys.forEach(key => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Failed to remove ${key}:`, error);
    }
  });
}

/**
 * Get settings summary for display
 */
export function getSettingsSummary() {
  const settings = getUserSettings();
  return {
    displayName: settings.displayName,
    storageType: '本地浏览器',
    syncEnabled: false,
  };
}

/**
 * React hooks for accessing application data
 * Provides reactive state management backed by localStorage
 */

import { useState, useEffect, useCallback } from 'react';
import type { Meeting, SummaryTemplate, ActionItem } from '../types/models';
import {
  meetingStorage,
  templateStorage,
  actionItemStorage,
} from '../lib/storage';

// Meetings hook
export function useMeetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setMeetings(meetingStorage.getAll());
    setLoading(false);
  }, []);

  const refresh = useCallback(() => {
    setMeetings(meetingStorage.getAll());
  }, []);

  const createMeeting = useCallback((data: Omit<Meeting, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newMeeting = meetingStorage.create(data);
    refresh();
    return newMeeting;
  }, [refresh]);

  const updateMeeting = useCallback((id: string, patch: Partial<Omit<Meeting, 'id' | 'createdAt'>>) => {
    const updated = meetingStorage.update(id, patch);
    if (updated) refresh();
    return updated;
  }, [refresh]);

  const deleteMeeting = useCallback((id: string) => {
    const deleted = meetingStorage.delete(id);
    if (deleted) refresh();
    return deleted;
  }, [refresh]);

  const getMeetingById = useCallback((id: string) => {
    return meetingStorage.getById(id);
  }, []);

  const getRecentMeetings = useCallback((limit: number = 5) => {
    return meetingStorage.getRecent(limit);
  }, []);

  return {
    meetings,
    loading,
    refresh,
    createMeeting,
    updateMeeting,
    deleteMeeting,
    getMeetingById,
    getRecentMeetings,
  };
}

// Templates hook
export function useTemplates() {
  const [templates, setTemplates] = useState<SummaryTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTemplates(templateStorage.getAll());
    setLoading(false);
  }, []);

  const refresh = useCallback(() => {
    setTemplates(templateStorage.getAll());
  }, []);

  const createTemplate = useCallback((data: Omit<SummaryTemplate, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newTemplate = templateStorage.create(data);
    refresh();
    return newTemplate;
  }, [refresh]);

  const updateTemplate = useCallback((id: string, patch: Partial<Omit<SummaryTemplate, 'id' | 'createdAt'>>) => {
    const updated = templateStorage.update(id, patch);
    if (updated) refresh();
    return updated;
  }, [refresh]);

  const deleteTemplate = useCallback((id: string) => {
    const deleted = templateStorage.delete(id);
    if (deleted) refresh();
    return deleted;
  }, [refresh]);

  const setDefaultTemplate = useCallback((id: string) => {
    const updated = templateStorage.setDefault(id);
    if (updated) refresh();
    return updated;
  }, [refresh]);

  const getDefaultTemplate = useCallback(() => {
    return templateStorage.getDefault();
  }, []);

  const getTemplateById = useCallback((id: string) => {
    return templateStorage.getById(id);
  }, []);

  return {
    templates,
    loading,
    refresh,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    setDefaultTemplate,
    getDefaultTemplate,
    getTemplateById,
  };
}

// Action items hook
export function useActionItems() {
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setActionItems(actionItemStorage.getAll());
    setLoading(false);
  }, []);

  const refresh = useCallback(() => {
    setActionItems(actionItemStorage.getAll());
  }, []);

  const createActionItem = useCallback((data: Omit<ActionItem, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newItem = actionItemStorage.create(data);
    refresh();
    return newItem;
  }, [refresh]);

  const updateActionItem = useCallback((id: string, patch: Partial<Omit<ActionItem, 'id' | 'createdAt'>>) => {
    const updated = actionItemStorage.update(id, patch);
    if (updated) refresh();
    return updated;
  }, [refresh]);

  const deleteActionItem = useCallback((id: string) => {
    const deleted = actionItemStorage.delete(id);
    if (deleted) refresh();
    return deleted;
  }, [refresh]);

  const getActionItemsByMeetingId = useCallback((meetingId: string) => {
    return actionItemStorage.getByMeetingId(meetingId);
  }, []);

  return {
    actionItems,
    loading,
    refresh,
    createActionItem,
    updateActionItem,
    deleteActionItem,
    getActionItemsByMeetingId,
  };
}

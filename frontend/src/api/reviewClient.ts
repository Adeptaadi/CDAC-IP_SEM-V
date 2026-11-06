import { request } from './client';

export interface PendingReview {
  review_id: string;
  investigation_id: string;
  requested_action: string;
  risk_level: string;
  status: string;
  created_at: string;
}

export interface ReviewSubmission {
  decision: 'approve' | 'reject' | 'modify';
  analyst_id: string;
  analyst_comments?: string;
  modified_action?: string;
}

export const reviewClient = {
  /**
   * Lists pending human reviews requiring analyst adjudication
   * GET /api/reviews/pending
   */
  listPendingReviews: (): Promise<PendingReview[]> => {
    return request<PendingReview[]>({
      method: 'GET',
      url: '/api/reviews/pending',
    });
  },

  /**
   * Submits analyst approval, rejection, or modification on a review item
   * POST /api/reviews/{review_id}/decision
   */
  submitDecision: (reviewId: string, submission: ReviewSubmission): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: `/api/reviews/${reviewId}/decision`,
      data: submission,
    });
  },

  /**
   * Simulates containment action computing blast radius, disruption, and rollback
   * POST /api/reviews/simulate
   */
  simulateAction: (actionName: string, targetEntities: string[]): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: '/api/reviews/simulate',
      data: {
        action_name: actionName,
        target_entities: targetEntities,
      },
    });
  },
};

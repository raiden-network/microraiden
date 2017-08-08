import { TestBed, inject } from '@angular/core/testing';

import { RMPService } from './rmp.service';

describe('RMPService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [RMPService]
    });
  });

  it('should be created', inject([RMPService], (service: RMPService) => {
    expect(service).toBeTruthy();
  }));
});

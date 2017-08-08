import { RaidenMicropaymentsClientPage } from './app.po';

describe('raiden-micropayments-client App', () => {
  let page: RaidenMicropaymentsClientPage;

  beforeEach(() => {
    page = new RaidenMicropaymentsClientPage();
  });

  it('should display welcome message', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('Welcome to app!');
  });
});

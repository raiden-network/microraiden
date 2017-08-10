import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable } from "rxjs/Observable";
import { Subscription } from "rxjs/Subscription";
import { FormGroup, FormControl, FormBuilder } from "@angular/forms";

import { RMPConfig } from './services/rmp.config';
import { RMPService } from './services/rmp.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];
  title = 'Raiden Micropayments Service Client';
  accounts: string[];
  form: FormGroup;
  signed$: Observable<string>;

  constructor(private config: RMPConfig,
              private rmp: RMPService,
              private fb: FormBuilder) {
    this.form = this.fb.group({
      account: '',
      message: null,
    })
  }

  ngOnInit() {
    this.rmp.getAccounts()
      .subscribe((accounts) => {
        this.accounts = accounts;
        this.form.get('account').setValue(accounts[0]);
      });
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  onFormSubmit() {
    this.signed$ = this.rmp.signHash(this.form.value.message, this.form.value.account);
  }
}

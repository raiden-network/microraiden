import { BrowserModule } from '@angular/platform-browser';
import { NgModule, APP_INITIALIZER } from '@angular/core';
import { HttpClientModule } from '@angular/common/http'
import { ReactiveFormsModule } from '@angular/forms'

import { environment  } from '../environments/environment';

import { AppComponent } from './app.component';
import { RMPConfig } from './services/rmp.config';
import { RMPService } from './services/rmp.service';


export function ConfigLoader(rmpConfig: RMPConfig) {
  // Note: this factory need to return a function (that return a promise)
  return () => rmpConfig.load(environment.configFile);
}

@NgModule({
  declarations: [
    AppComponent,
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    ReactiveFormsModule,
  ],
  providers: [
    RMPConfig,
    {
      provide: APP_INITIALIZER,
      useFactory: ConfigLoader,
      deps: [RMPConfig],
      multi: true
    },
    RMPService,
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
